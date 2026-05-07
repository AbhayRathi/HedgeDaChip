from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.apu_params import (
    DEFAULT_IMBALANCE_THRESHOLD,
    DEFAULT_MAX_ORDERS_PER_WINDOW,
    DEFAULT_SPREAD_THRESHOLD,
)
from sw_golden.compare import GoldenComparator
from sw_golden.models import Event, decode_output_frame, encode_event_frame, encode_output_frame, end_to_end_model

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'end2end'


def sources():
    return [
        str(RTL / 'pkg/apu_params.sv'),
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'ifc/vr_if.sv'),
        str(RTL / 'util/fifo.sv'),
        str(RTL / 'util/timestamp.sv'),
        str(RTL / 'util/perf_counters.sv'),
        str(RTL / 'ingress/stream_rx.sv'),
        str(RTL / 'ingress/parser.sv'),
        str(RTL / 'state/ob_mem.sv'),
        str(RTL / 'state/pim_prims.sv'),
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
    dut.spread_threshold.value = DEFAULT_SPREAD_THRESHOLD
    dut.imbalance_threshold.value = DEFAULT_IMBALANCE_THRESHOLD
    dut.max_orders_per_window.value = DEFAULT_MAX_ORDERS_PER_WINDOW
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    while not dut.in_ready.value:
        await RisingEdge(dut.clk)


async def run_replay(dut, events, out_ready_pattern=None):
    outputs = []
    latencies = []
    accepted_cycles = []
    cycle = 0
    in_index = 0
    out_ready_pattern = out_ready_pattern or [1, 1, 0, 1, 1, 1, 0, 1]
    while len(outputs) < len(events):
        dut.out_ready.value = out_ready_pattern[cycle % len(out_ready_pattern)]
        if in_index < len(events):
            dut.in_valid.value = 1
            dut.in_data.value = encode_event_frame(events[in_index])
        else:
            dut.in_valid.value = 0
        await RisingEdge(dut.clk)
        if int(dut.in_valid.value) and int(dut.in_ready.value):
            accepted_cycles.append(cycle)
            in_index += 1
        if int(dut.out_valid.value) and int(dut.out_ready.value):
            outputs.append(dut.out_data.value.integer)
            latencies.append(cycle - accepted_cycles[len(outputs) - 1])
        cycle += 1
        assert cycle < 400
    dut.in_valid.value = 0
    return outputs, latencies


@cocotb.test()
async def end_to_end_matches_golden_and_is_deterministic(dut):
    comparator = GoldenComparator()
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    events = [
        Event(1, 0, 100, 8, ts=1),
        Event(1, 1, 105, 2, ts=2),
        Event(4, 0, 101, 10, ts=3),
        Event(3, 1, 105, 1, ts=4),
        Event(2, 0, 101, 3, ts=5),
    ]
    expected_actions = end_to_end_model(events, DEFAULT_SPREAD_THRESHOLD, DEFAULT_IMBALANCE_THRESHOLD, DEFAULT_MAX_ORDERS_PER_WINDOW)
    expected_frames = [decode_output_frame(encode_output_frame(action)) for action in expected_actions]

    await reset_dut(dut)
    outputs_a, latencies_a = await run_replay(dut, events)
    actual_frames_a = [decode_output_frame(bits) for bits in outputs_a]
    report = comparator.compare_fields(
        actual_frames_a,
        expected_frames,
        ['action_type', 'price', 'qty', 'reason_code', 'timestamp', 'checksum'],
        input_events=events,
        label='output_frames',
    )
    assert report['pass'], comparator.format_report(report)
    assert max(latencies_a) <= 20

    await reset_dut(dut)
    outputs_b, latencies_b = await run_replay(dut, events)
    actual_frames_b = [decode_output_frame(bits) for bits in outputs_b]
    report = comparator.compare_fields(
        actual_frames_b,
        expected_frames,
        ['action_type', 'price', 'qty', 'reason_code', 'timestamp', 'checksum'],
        input_events=events,
        label='repeat_output_frames',
    )
    assert report['pass'], comparator.format_report(report)
    assert outputs_b == outputs_a
    assert latencies_b == latencies_a


@cocotb.test()
async def ingress_fifo_absorbs_burst_without_drop(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    events = [Event(1 if idx % 2 == 0 else 4, idx % 2, 100 + idx, idx + 1, ts=idx + 1) for idx in range(10)]
    await reset_dut(dut)
    outputs, _ = await run_replay(dut, events, out_ready_pattern=[0, 0, 1, 1, 0, 1])
    assert len(outputs) == len(events), f'expected {len(events)} frames, got {len(outputs)}'
    assert int(dut.fifo_max_occupancy.value) >= 1


def test_end2end():
    run(
        verilog_sources=sources(),
        toplevel='apu_top',
        module='test_end2end',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
    )
