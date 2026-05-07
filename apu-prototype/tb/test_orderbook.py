from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.models import Event, OrderBookModel, encode_event_frame, encode_feature, parse_event_frame

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'


def sources():
    return [
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'state/ob_engine.sv'),
    ]


@cocotb.test()
async def orderbook_matches_golden(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    stream = [
        Event(1, 0, 100, 9, 1),
        Event(1, 1, 104, 3, 2),
        Event(4, 0, 101, 12, 3),
        Event(3, 0, 101, 2, 4),
        Event(2, 1, 104, 3, 5),
    ]
    model = OrderBookModel()
    for event in stream:
        parsed = parse_event_frame(encode_event_frame(event))
        expected = model.apply(parsed)
        dut.in_event_data.value = encode_event_frame(parsed)
        dut.in_valid.value = 1
        while not dut.in_ready.value:
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.in_valid.value = 0
        while not dut.out_valid.value:
            await RisingEdge(dut.clk)
        assert dut.out_feature_data.value.integer == encode_feature(expected)
        await RisingEdge(dut.clk)


def test_orderbook():
    run(
        verilog_sources=sources(),
        toplevel='ob_engine',
        module='test_orderbook',
        sim_build=str(ROOT / 'sim_build/orderbook'),
        simulator='verilator',
        extra_args=['--sv'],
    )
