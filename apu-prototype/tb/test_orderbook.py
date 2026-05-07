from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.compare import GoldenComparator
from sw_golden.models import Event, OrderBookModel, decode_feature, encode_event_frame, parse_event_frame

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'orderbook'


def sources():
    return [
        str(RTL / 'pkg/apu_params.sv'),
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'state/pim_prims.sv'),
        str(RTL / 'state/ob_mem.sv'),
        str(RTL / 'state/ob_engine.sv'),
    ]


@cocotb.test()
async def orderbook_matches_golden_and_uses_bram_latency(dut):
    comparator = GoldenComparator()
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    ready_wait = 0
    while not dut.in_ready.value:
        await RisingEdge(dut.clk)
        ready_wait += 1
        assert ready_wait < 20, 'ob_engine never became ready after reset'

    stream = [
        Event(1, 0, 100, 9, ts=1),
        Event(1, 1, 104, 3, ts=2),
        Event(4, 0, 101, 12, ts=3),
        Event(3, 0, 101, 2, ts=4),
        Event(2, 1, 104, 3, ts=5),
    ]
    model = OrderBookModel()
    actual = []
    expected = []
    latencies = []
    cycle = 0
    accepted_cycle = None
    for event in stream:
        parsed = parse_event_frame(encode_event_frame(event))
        expected.append(model.apply(parsed))
        dut.in_event_data.value = encode_event_frame(parsed)
        dut.in_valid.value = 1
        wait_cycles = 0
        while not dut.in_ready.value:
            await RisingEdge(dut.clk)
            cycle += 1
            wait_cycles += 1
            assert wait_cycles < 20, 'ob_engine stalled unexpectedly before accepting an event'
        await RisingEdge(dut.clk)
        accepted_cycle = cycle
        cycle += 1
        dut.in_valid.value = 0
        wait_cycles = 0
        while not dut.out_valid.value:
            await RisingEdge(dut.clk)
            cycle += 1
            wait_cycles += 1
            assert wait_cycles < 20, f'ob_engine did not emit a feature for event {event}'
        latencies.append(cycle - accepted_cycle)
        actual.append(decode_feature(dut.out_feature_data.value.integer))
        await RisingEdge(dut.clk)
        cycle += 1

    report = comparator.compare_features(actual, expected, input_events=stream)
    assert report['pass'], comparator.format_report(report)
    assert all(latency == 3 for latency in latencies), f'expected deterministic BRAM-delayed latency of 3 observed cycles, got {latencies}'


def test_orderbook():
    run(
        verilog_sources=sources(),
        toplevel='ob_engine',
        module='test_orderbook',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
    )
