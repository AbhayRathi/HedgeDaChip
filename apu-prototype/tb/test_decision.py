from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.apu_params import DEFAULT_IMBALANCE_THRESHOLD, DEFAULT_SPREAD_THRESHOLD
from sw_golden.compare import GoldenComparator
from sw_golden.models import Feature, compute_order_qty, decode_action, decision_model, encode_feature

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'decision'


def sources():
    return [
        str(RTL / 'pkg/apu_params.sv'),
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'deterministic/decision_pipe.sv'),
    ]


@cocotb.test()
async def decision_matches_golden_and_sizes_qty(dut):
    comparator = GoldenComparator()
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.spread_threshold.value = DEFAULT_SPREAD_THRESHOLD
    dut.imbalance_threshold.value = DEFAULT_IMBALANCE_THRESHOLD
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    features = [
        Feature(best_bid_price=100, best_bid_qty=12, best_ask_price=110, best_ask_qty=10, spread=10, imbalance=2, event_ts=11),
        Feature(best_bid_price=100, best_bid_qty=12, best_ask_price=105, best_ask_qty=8, spread=5, imbalance=5, event_ts=12),
        Feature(best_bid_price=100, best_bid_qty=70, best_ask_price=105, best_ask_qty=6, spread=5, imbalance=64, event_ts=13),
        Feature(best_bid_price=100, best_bid_qty=2, best_ask_price=101, best_ask_qty=4, spread=1, imbalance=-2, event_ts=14),
    ]
    expected = [decision_model(f, DEFAULT_SPREAD_THRESHOLD, DEFAULT_IMBALANCE_THRESHOLD) for f in features]
    actual = []

    for feature in features:
        dut.in_feature_data.value = encode_feature(feature)
        dut.in_valid.value = 1
        wait_cycles = 0
        while not dut.in_ready.value:
            await RisingEdge(dut.clk)
            wait_cycles += 1
            assert wait_cycles < 20, 'decision_pipe stalled before accepting a feature'
        await RisingEdge(dut.clk)
        if dut.out_valid.value:
            actual.append(decode_action(dut.out_action_data.value.integer))
        dut.in_valid.value = 0

    for _ in range(len(expected) + 8):
        await RisingEdge(dut.clk)
        if dut.out_valid.value:
            actual.append(decode_action(dut.out_action_data.value.integer))
    assert len(actual) == len(expected), f'decision_pipe emitted {len(actual)} actions for {len(expected)} features'

    report = comparator.compare_actions(actual, expected, input_events=features)
    assert report['pass'], comparator.format_report(report)
    assert expected[0].qty == 1 == compute_order_qty(features[0], DEFAULT_IMBALANCE_THRESHOLD)
    assert expected[1].qty == 4 == compute_order_qty(features[1], DEFAULT_IMBALANCE_THRESHOLD)
    assert expected[2].qty == 16 == compute_order_qty(features[2], DEFAULT_IMBALANCE_THRESHOLD)


def test_decision():
    run(
        verilog_sources=sources(),
        toplevel='decision_pipe',
        module='test_decision',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
    )
