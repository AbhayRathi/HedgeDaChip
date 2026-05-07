from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.apu_params import DEFAULT_WINDOW_CYCLES
from sw_golden.compare import GoldenComparator
from sw_golden.models import Action, RiskModel, decode_action, encode_action

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'risk'


def sources():
    return [
        str(RTL / 'pkg/apu_params.sv'),
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'risk/risk_engine.sv'),
    ]


@cocotb.test()
async def risk_enforces_invariants(dut):
    comparator = GoldenComparator()
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.kill_switch.value = 0
    dut.max_orders_per_window.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    actions = [
        Action(1, 100, 1, 1, timestamp=1),
        Action(1, 100, 1, 1, timestamp=2),
        Action(1, 0, 1, 1, timestamp=3),
        Action(1, 100, 0, 1, timestamp=4),
    ]
    model = RiskModel(max_orders_per_window=1, window_cycles=DEFAULT_WINDOW_CYCLES)
    expected = [model.step(action) for action in actions]
    actual = []

    for action in actions:
        dut.in_action_data.value = encode_action(action)
        dut.in_valid.value = 1
        wait_cycles = 0
        while not dut.in_ready.value:
            await RisingEdge(dut.clk)
            wait_cycles += 1
            assert wait_cycles < 20, 'risk_engine stalled before accepting an action'
        await RisingEdge(dut.clk)
        if dut.out_valid.value:
            actual.append(decode_action(dut.out_action_data.value.integer))
        dut.in_valid.value = 0

    wait_cycles = 0
    while len(actual) < len(expected):
        await RisingEdge(dut.clk)
        wait_cycles += 1
        assert wait_cycles < 40, 'risk_engine did not emit all expected actions'
        if dut.out_valid.value:
            actual.append(decode_action(dut.out_action_data.value.integer))

    report = comparator.compare_actions(actual, expected, input_events=actions)
    assert report['pass'], comparator.format_report(report)

    dut.kill_switch.value = 1
    blocked = Action(1, 100, 1, 1, timestamp=9)
    dut.in_action_data.value = encode_action(blocked)
    dut.in_valid.value = 1
    wait_cycles = 0
    while not dut.in_ready.value:
        await RisingEdge(dut.clk)
        wait_cycles += 1
        assert wait_cycles < 20, 'risk_engine stalled before kill-switch action'
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    wait_cycles = 0
    while not dut.out_valid.value:
        await RisingEdge(dut.clk)
        wait_cycles += 1
        assert wait_cycles < 20, 'risk_engine did not emit the kill-switch response'
    actual_blocked = [decode_action(dut.out_action_data.value.integer)]
    expected_blocked = [Action(reason_code=0x10, timestamp=9)]
    report = comparator.compare_actions(actual_blocked, expected_blocked, input_events=[blocked])
    assert report['pass'], comparator.format_report(report)


def test_risk():
    run(
        verilog_sources=sources(),
        toplevel='risk_engine',
        module='test_risk',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
    )
