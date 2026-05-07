from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.models import Event, encode_action, encode_event_frame, end_to_end_model

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'


def sources():
    return [
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'util/timestamp.sv'),
        str(RTL / 'util/perf_counters.sv'),
        str(RTL / 'ingress/stream_rx.sv'),
        str(RTL / 'ingress/parser.sv'),
        str(RTL / 'state/ob_engine.sv'),
        str(RTL / 'deterministic/decision_pipe.sv'),
        str(RTL / 'risk/risk_engine.sv'),
        str(RTL / 'egress/order_encoder.sv'),
        str(RTL / 'apu_top.sv'),
    ]


async def reset_dut(dut):
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.kill_switch.value = 0
    dut.stamp_ts.value = 0
    dut.spread_threshold.value = 2
    dut.imbalance_threshold.value = 2
    dut.max_orders_per_window.value = 4
    await RisingEdge(dut.clk)
    dut.rst.value = 0


async def run_replay(dut, events):
    outputs = []
    latencies = []
    accepted_cycles = []
    cycle = 0
    in_index = 0
    out_ready_pattern = [1, 1, 0, 1, 1, 1, 0, 1]
    while len(outputs) < len(events):
        dut.out_ready.value = out_ready_pattern[cycle % len(out_ready_pattern)]
        if in_index < len(events):
            dut.in_valid.value = 1
            dut.in_data.value = encode_event_frame(events[in_index])
        else:
            dut.in_valid.value = 0
        await RisingEdge(dut.clk)
        if dut.in_valid.value and dut.in_ready.value:
            accepted_cycles.append(cycle)
            in_index += 1
        if dut.out_valid.value and dut.out_ready.value:
            outputs.append(dut.out_data.value.integer)
            latencies.append(cycle - accepted_cycles[len(outputs) - 1])
        cycle += 1
        assert cycle < 200
    dut.in_valid.value = 0
    return outputs, latencies


@cocotb.test()
async def end_to_end_matches_golden_and_is_deterministic(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    events = [
        Event(1, 0, 100, 8, 1),
        Event(1, 1, 105, 2, 2),
        Event(4, 0, 101, 10, 3),
        Event(3, 1, 105, 1, 4),
        Event(2, 0, 101, 3, 5),
    ]
    expected = [encode_action(action) for action in end_to_end_model(events, 2, 2, 4)]

    await reset_dut(dut)
    outputs_a, latencies_a = await run_replay(dut, events)
    assert outputs_a == expected
    assert max(latencies_a) <= 20

    await reset_dut(dut)
    outputs_b, latencies_b = await run_replay(dut, events)
    assert outputs_b == outputs_a
    assert latencies_b == latencies_a


def test_end2end():
    run(
        verilog_sources=sources(),
        toplevel='apu_top',
        module='test_end2end',
        sim_build=str(ROOT / 'sim_build/end2end'),
        simulator='verilator',
        extra_args=['--sv'],
    )
