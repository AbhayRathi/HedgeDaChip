# GIGABRIEF — APU Prototype (Agent Processing Unit)

Memory-Centric, Deterministic, Agentic Hardware Pipeline (FPGA-first, ASIC-ready)

## 0) Mission / Intent

Build an FPGA-prototyped Agent Processing Unit (APU) that demonstrates:

- deterministic low-latency streaming pipelines with bounded worst-case latency and low jitter
- memory-centric compute that minimizes data movement and emulates PIM/CIM behavior now with a path to SRAM-CIM later
- agentic workflow enablement, where policy, config, and weights can update frequently with minimal manual intervention
- non-bypassable safety and risk gating where hardwired invariants and a hard override always win
- a clear path from RTL simulation to FPGA prototype and later chiplet / ASIC mapping

Primary MVP use case: trading-like event streams with architecture generalizable to telemetry, alerts, and agent state machines.

## 1) Big Picture Architecture (Reference)

Pipeline blocks:

- Ingress: host replay stream receiver (MVP), later NIC / Ethernet
- Parser / Decoder: hardware FSM parses fixed event frames
- State / Orderbook Engine: BRAM / SRAM-like memory with update logic and feature extraction
- Deterministic Decision Pipeline: fixed-K stage pipeline (reflex path)
- Future ML Inference Tile: quantized advisor path
- Future Agent Controller: FSM and later RISC-V soft core
- Risk Engine: final gate with hard override and limits
- Egress: order / action encoder to host stream first, later NIC TX

Two conceptual paths:

- Reflex path: `State -> Decision -> Risk -> Output`
- Advisor path: `State features -> ML -> Controller -> config/weights updates`

Risk is always authoritative.

## 2) MVP v1 Scope

Required MVP vertical slice:

`Host replay stream -> Parser -> State/Orderbook (BRAM) -> Decision (fixed pipeline) -> Risk gate -> Output stream`

Not in MVP v1:

- real Ethernet ingest / DPDK / drivers
- ML tile
- agent controller CPU
- multi-clock CDC complexity

MVP v1 must deliver:

- end-to-end correctness against a software golden model
- deterministic latency measured in cycles
- risk invariants enforced

Defaults:

- host replay input first
- top-of-book first, then scale to N-level
- one clock domain on the critical path
- synchronous reset
- 128-bit stream beat width

## 3) Design Principles

- Determinism: bounded worst-case cycles, no unbounded variable-latency critical-path behavior
- Streaming valid/ready everywhere
- Test-driven hardware with cocotb + golden model checks
- Modularity with clean replaceable boundaries
- Safety first: risk is final and non-bypassable
- Instrumentation: counters, timestamps, stalls, queue depth metrics
- ASIC-ready memory-centric interfaces

## 4) Repository Layout

The brief requested this structure under `apu-prototype/`, including:

- `docs/00_GIGABRIEF.md` through `docs/08_coding_standards.md`
- `rtl/apu_top.sv`
- packages under `rtl/pkg/`
- interfaces under `rtl/ifc/`
- ingress, state, deterministic, risk, egress, and util RTL subdirectories
- cocotb tests under `tb/`
- golden model under `sw_golden/`
- simulation runners under `sim/`
- FPGA placeholders under `fpga/`
- GitHub Actions CI under `.github/workflows/ci.yml`

## 5) Interface Contracts

### 5.1 Stream interface (`vr_if.sv`)

Required signals:

- `valid`, `ready`
- `data[W-1:0]`
- optional `last`
- optional `user[U-1:0]`

Rules:

- transfer on `valid && ready`
- data stable while `valid=1` and `ready=0`
- backpressure allowed everywhere
- no data loss unless explicitly designed by a bounded FIFO

### 5.2 MMIO control plane (`mmio_if.sv`)

Expose shapes for:

- thresholds
- risk limits
- hard override
- model select / config
- counter readback

MVP can use direct top-level inputs while keeping interface shape stable.

## 6) Event Schema

Fixed 128-bit single-beat event for host replay.

`event_t` fields:

- `event_type[7:0]`: `0=NOP`, `1=ADD`, `2=CANCEL`, `3=TRADE`, `4=UPDATE`
- `side[0]`: `0=bid`, `1=ask`
- `price[31:0]`: signed fixed-point placeholder
- `qty[31:0]`
- `ts[31:0]`
- `flags[22:0]`

`feature_t` fields:

- best bid price / qty
- best ask price / qty
- spread
- imbalance
- last trade price / qty

`action_t` fields:

- `action_type`
- `price`
- `qty`
- `reason_code`

## 7) Determinism Definition

Deterministic means bounded worst-case latency in cycles under all supported patterns, including bursts and backpressure. Critical-path rules:

- bounded FIFOs only
- no unbounded data-dependent loops
- no variable-latency memory behavior on the reflex path
- documented latency budgets per module

## 8) Timing Budget

Targets documented by the brief:

- `stream_rx`: 0-1 cycles buffering
- `parser`: <= 4 cycles per event
- `ob_engine`: <= 6 cycles update/features
- `decision_pipe`: fixed K cycles
- `risk_engine`: <= 1-2 cycles
- `order_encoder`: <= 2 cycles
- total reflex path target: <= 20 cycles for the MVP

## 9) Module Behavior Specs

Modules requested and implemented in the scaffold:

- `stream_rx.sv`: host replay ingress, optional timestamp stamping
- `parser.sv`: 128-bit frame to `event_t`, deterministic invalid-event handling
- `ob_mem.sv`: BRAM / SRAM-like synchronous memory wrapper
- `pim_prims.sv`: memory-adjacent compare / min / max helper API
- `ob_engine.sv`: deterministic top-of-book state + feature generation
- `decision_pipe.sv`: fixed pipeline for spread / imbalance policy
- `risk_engine.sv`: final hard gate with override, rate limit, and sanity checks
- `order_encoder.sv`: deterministic 128-bit action frame builder
- `timestamp.sv`: free-running cycle counter
- `fifo.sv`: bounded valid/ready FIFO
- `perf_counters.sv`: minimal counters for accepted, emitted, and stalled traffic
- `apu_top.sv`: integration of the MVP reflex path

## 10) Verification Strategy

The brief requires cocotb plus a Python golden model as source of truth. Required tests:

- parser field extraction and backpressure stability
- orderbook / feature extraction checks
- exact decision output checks
- risk hard-override, rate limiting, and sanity checks
- end-to-end replay, action-sequence comparison, latency bound, and determinism checks

## 11) CI / Automation

Required CI work:

- lint / compile checks for SystemVerilog
- Verilator build plus cocotb tests
- runnable project scripts under `sim/verilator/run.sh` and `sim/cocotb/run.sh`

## 12) Coding Standards

- `always_ff` for sequential logic
- `always_comb` for combinational logic
- no inferred latches
- synchronous active-high reset
- parameterized widths and depths
- each module documents purpose, interface, latency, and backpressure behavior

## 13) Definition of Done

A module is done only when it passes unit tests, matches the golden model where applicable, has documented latency bounds, has no known invariant violations, and passes integration when part of the vertical slice.

## 14) Differentiating Design Edges

- reflex + advisor split
- memory-local feature extraction
- safety-first enforcement
- chiplet-ready boundaries for later partitioning

## 15) Roadmap

- Phase 0: repo scaffolding + interfaces + CI
- Phase 1: MVP v1 vertical slice
- Phase 2: N-level orderbook + expanded PIM
- Phase 3: ML tile
- Phase 4: controller / policy manager
- Phase 5: real NIC integration
- Phase 6: ASIC / chiplet mapping exploration

## 16) Defaults

- 128-bit stream beats
- single clock domain
- synchronous active-high reset
- top-of-book orderbook
- threshold-based spread and imbalance strategy
- 128-bit host-visible action output frames

## 17) Important Non-Goals

- real exchange protocol parsing
- kernel-bypass drivers / DPDK
- on-chip training / RL training
- transformer inference
- multi-clock complexity
- tapeout itself

## 18) Immediate Build Order

The brief asked for the scaffold, packages and interfaces first, then ingress/parser, state/orderbook, decision, risk, encoding, top-level integration, golden model, cocotb tests, simulation scripts, and CI.

## 19) Output Expectations

At the end of MVP v1 the system should be able to:

- feed an event replay
- produce deterministic action outputs
- verify correctness against the golden model
- measure latency in cycles
- inspect counters and stall metrics

## 20) Notes for Copilot

- prefer SystemVerilog packages, types, and interfaces
- every module must compile under Verilator
- favor simple, correct deterministic designs over clever ones
- keep the PIM interface stable even if implemented in plain logic first
