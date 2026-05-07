# MVP phases

This roadmap keeps the design incremental: each phase must remain testable in simulation and must preserve the deterministic reflex-path contract unless the phase explicitly extends it.

## Phase 0 — Repository scaffolding and contracts

**Status:** complete in this PR branch.

Acceptance criteria:

- repository layout exists under `apu-prototype/`
- shared RTL packages and interfaces compile
- golden model and cocotb infrastructure are present
- CI can lint and run regression tests

## Phase 1 — Reflex-path MVP vertical slice

**Status:** complete in the current branch.

Acceptance criteria:

- host replay enters through `stream_rx`
- parser, orderbook, decision, risk, and encoder are connected in `apu_top`
- output frames are explicit and host-decodable
- end-to-end tests prove determinism and latency bounds in cycles

## Phase 2 — Memory-centric hardening

**Status:** complete in this task.

Acceptance criteria:

- `ob_engine` stores bid/ask top-of-book state through `ob_mem`
- `pim_prims` is used by the orderbook stage instead of inline price-policy logic
- ingress FIFO is live and covered by burst tests
- shared APU parameters are mirrored between RTL and Python tests

## Phase 3 — Advisor-path preparation

**Target:** next major iteration.

Acceptance criteria:

- add an ML-tile stub with bounded-latency handshake interfaces
- define weights/config memory contracts and safe-swap semantics
- keep the reflex path authoritative and independently verifiable
- preserve deterministic risk gating regardless of advisor availability

## Phase 4 — FPGA targeting collateral

**Target:** after the simulator-only MVP is stable.

Acceptance criteria:

- populate `fpga/constraints/` with board timing and pin constraints
- add a reproducible vendor flow entrypoint under `fpga/xilinx_vivado/`
- document clock/reset assumptions and board IO mapping
- produce an implementation build that preserves the same stream and output contracts used in simulation

## Phase 5 and beyond

Later work includes deeper orderbook state, richer PIM/CIM emulation, real NIC ingress/egress, and eventual chiplet or ASIC partition studies. Each later phase should reuse the same golden-model-first workflow so hardware changes remain explainable and regression-friendly.
