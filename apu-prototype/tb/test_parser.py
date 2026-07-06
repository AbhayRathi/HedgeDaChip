from __future__ import annotations

import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from sw_golden.compare import GoldenComparator
from sw_golden.models import Event, encode_event_frame, parse_event_frame

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'
SIM_BUILD = ROOT / 'sim' / 'cocotb' / 'build' / 'parser'


def sources():
    return [
        str(RTL / 'pkg/apu_params.sv'),
        str(RTL / 'pkg/apu_types.sv'),
        str(RTL / 'ifc/vr_if.sv'),
        str(RTL / 'ingress/parser.sv'),
        str(RTL / 'ingress/parser_tb.sv'),
    ]


@cocotb.test()
async def parser_matches_golden(dut):
    comparator = GoldenComparator()
    cocotb.start_soon(Clock(dut.clk, 1, units='ns').start())
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    events = [
        Event(random.randint(0, 4), random.randint(0, 1), random.randint(-50, 200), random.randint(0, 20), ts=i)
        for i in range(1, 6)
    ]
    events.append(Event(9, 1, 77, 3, ts=99))

    actual = []
    expected = []
    for event in events:
        frame = encode_event_frame(event)
        dut.in_data.value = frame
        dut.in_valid.value = 1
        while not dut.in_ready.value:
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.in_valid.value = 0
        while not dut.out_valid.value:
            await RisingEdge(dut.clk)
        actual.append(parse_event_frame(dut.out_event_data.value.integer))
        expected.append(parse_event_frame(frame))

    report = comparator.compare_events(actual, expected, input_events=events)
    assert report['pass'], comparator.format_report(report)

    event = Event(1, 0, 101, 7, ts=33)
    dut.in_data.value = encode_event_frame(event)
    dut.in_valid.value = 1
    while not dut.in_ready.value:
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    while not dut.out_valid.value:
        await RisingEdge(dut.clk)
    dut.out_ready.value = 0
    held = dut.out_event_data.value.integer
    for _ in range(3):
        await RisingEdge(dut.clk)
        assert dut.out_event_data.value.integer == held
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)


def test_parser():
    run(
        verilog_sources=sources(),
        toplevel='parser_tb',
        module='test_parser',
        sim_build=str(SIM_BUILD),
        simulator='verilator',
        extra_args=['--sv', '--trace'],
        waves=True,
    )
