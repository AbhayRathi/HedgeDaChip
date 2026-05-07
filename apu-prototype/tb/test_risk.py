from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.models import Action, RiskModel, encode_action

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'


def sources():
    return [
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'risk/risk_engine.sv'),
    ]


@cocotb.test()
async def risk_enforces_invariants(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.kill_switch.value = 0
    dut.max_orders_per_window.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    actions = [
        Action(1, 100, 1, 1),
        Action(1, 100, 1, 1),
        Action(1, 0, 1, 1),
        Action(1, 100, 0, 1),
    ]
    model = RiskModel(max_orders_per_window=1)
    expected = [model.step(actions[0]), model.step(actions[1]), model.step(actions[2]), model.step(actions[3])]

    for action in actions:
        dut.in_action_data.value = encode_action(action)
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

    dut.kill_switch.value = 1
    dut.in_action_data.value = encode_action(Action(1, 100, 1, 1))
    dut.in_valid.value = 1
    while not dut.in_ready.value:
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    while not dut.out_valid.value:
        await RisingEdge(dut.clk)
    assert dut.out_action_data.value.integer == encode_action(Action(reason_code=0x10))


def test_risk():
    run(
        verilog_sources=sources(),
        toplevel='risk_engine',
        module='test_risk',
        sim_build=str(ROOT / 'sim_build/risk'),
        simulator='verilator',
        extra_args=['--sv'],
    )
