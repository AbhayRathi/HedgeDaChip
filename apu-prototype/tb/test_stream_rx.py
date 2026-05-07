from __future__ import annotations

from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.models import Event, encode_event_frame

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'stream_rx'


def sources():
    return [str(RTL / 'ingress/stream_rx.sv')]


@cocotb.test()
async def stream_rx_handles_handshake_and_timestamp_stamping(dut):
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.now_ts.value = 123
    dut.stamp_ts.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    event = Event(1, 0, 100, 5, ts=9)
    dut.in_data.value = encode_event_frame(event)
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    wait_cycles = 0
    while not dut.out_valid.value:
        await RisingEdge(dut.clk)
        wait_cycles += 1
        assert wait_cycles < 4, 'stream_rx did not present the first beat'
    assert int(dut.out_valid.value) == 1
    assert int(dut.out_data.value) == encode_event_frame(event)

    dut.out_ready.value = 0
    stamped = Event(1, 1, 101, 7, ts=0)
    dut.in_data.value = encode_event_frame(stamped)
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    while not dut.out_valid.value:
        await RisingEdge(dut.clk)
    held = int(dut.out_data.value)
    await RisingEdge(dut.clk)
    assert int(dut.out_data.value) == held, 'output must remain stable under backpressure'

    dut.out_ready.value = 1
    dut.stamp_ts.value = 1
    dut.now_ts.value = 321
    while int(dut.in_ready.value) == 0:
        await RisingEdge(dut.clk)
    dut.in_data.value = encode_event_frame(stamped)
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    wait_cycles = 0
    while not dut.out_valid.value:
        await RisingEdge(dut.clk)
        wait_cycles += 1
        assert wait_cycles < 4, 'stream_rx did not present the stamped beat'
    assert ((int(dut.out_data.value) >> 73) & 0xFFFF_FFFF) == 321


def test_stream_rx():
    run(
        verilog_sources=sources(),
        toplevel='stream_rx',
        module='test_stream_rx',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
    )
