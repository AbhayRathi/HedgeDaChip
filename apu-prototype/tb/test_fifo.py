from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'fifo'


def sources():
    return [str(RTL / 'util/fifo.sv')]


@cocotb.test()
async def fifo_handles_fill_and_drain(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.s_valid.value = 0
    dut.m_ready.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    assert int(dut.m_valid.value) == 0
    assert int(dut.occupancy.value) == 0

    payloads = [11, 22]
    for item in payloads:
        dut.s_data.value = item
        dut.s_valid.value = 1
        await RisingEdge(dut.clk)
    dut.s_valid.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.s_ready.value) == 0, 'FIFO should report full after two writes at DEPTH=2'
    assert int(dut.occupancy.value) == 2

    dut.s_valid.value = 1
    dut.s_data.value = 33
    await RisingEdge(dut.clk)
    dut.s_valid.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.occupancy.value) == 2, 'full write must not enqueue another item'

    dut.m_ready.value = 1
    seen = []
    while len(seen) < len(payloads):
        await RisingEdge(dut.clk)
        if dut.m_valid.value:
            seen.append(int(dut.m_data.value))
    assert seen == payloads, f'FIFO order violated, got {seen}'
    await RisingEdge(dut.clk)
    assert int(dut.occupancy.value) == 0


def test_fifo():
    run(
        verilog_sources=sources(),
        toplevel='fifo',
        module='test_fifo',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
        parameters={'WIDTH': 32, 'DEPTH': 2},
    )
