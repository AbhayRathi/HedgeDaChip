from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'perf_counters'


def sources():
    return [str(RTL / 'util/perf_counters.sv')]


@cocotb.test()
async def perf_counters_increment_and_wrap(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_fire.value = 0
    dut.out_fire.value = 0
    dut.stall.value = 0
    dut.occupancy.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    await RisingEdge(dut.clk)
    assert int(dut.in_count.value) == 0
    assert int(dut.out_count.value) == 0
    assert int(dut.stall_cycles.value) == 0

    dut.in_fire.value = 1
    dut.out_fire.value = 1
    dut.stall.value = 1
    dut.occupancy.value = 3
    await RisingEdge(dut.clk)
    dut.in_fire.value = 0
    dut.out_fire.value = 0
    dut.stall.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.in_count.value) == 1
    assert int(dut.out_count.value) == 1
    assert int(dut.stall_cycles.value) == 1
    assert int(dut.max_occupancy.value) == 3

    for _ in range(3):
        dut.in_fire.value = 1
        await RisingEdge(dut.clk)
    dut.in_fire.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.in_count.value) == 0, '2-bit counter should wrap after four increments total'


def test_perf_counters():
    run(
        verilog_sources=sources(),
        toplevel='perf_counters',
        module='test_perf_counters',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
        parameters={'COUNTER_W': 2, 'OCCUPANCY_W': 3},
    )
