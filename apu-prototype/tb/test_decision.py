from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.models import Action, Feature, decision_model, encode_action, encode_feature

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'


def sources():
    return [
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'deterministic/decision_pipe.sv'),
    ]


@cocotb.test()
async def decision_matches_golden(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.spread_threshold.value = 2
    dut.imbalance_threshold.value = 2
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    features = [
        Feature(best_bid_price=100, best_bid_qty=7, best_ask_price=104, best_ask_qty=2, spread=4, imbalance=5),
        Feature(best_bid_price=100, best_bid_qty=2, best_ask_price=104, best_ask_qty=8, spread=4, imbalance=-6),
        Feature(best_bid_price=100, best_bid_qty=4, best_ask_price=101, best_ask_qty=4, spread=1, imbalance=0),
    ]
    expected = [decision_model(f, 2, 2) for f in features]

    for feature in features:
        dut.in_feature_data.value = encode_feature(feature)
        dut.in_valid.value = 1
        while not dut.in_ready.value:
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.in_valid.value = 0

    seen = []
    while len(seen) < len(expected):
        await RisingEdge(dut.clk)
        if dut.out_valid.value:
            seen.append(dut.out_action_data.value.integer)
    assert seen == [encode_action(action) for action in expected]


def test_decision():
    run(
        verilog_sources=sources(),
        toplevel='decision_pipe',
        module='test_decision',
        sim_build=str(ROOT / 'sim_build/decision'),
        simulator='verilator',
        extra_args=['--sv'],
    )
