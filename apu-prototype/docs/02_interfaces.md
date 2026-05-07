# Interfaces

## Stream contract (`vr_if.sv`)

Each stream uses `valid`, `ready`, and `data`, with optional `last` and `user` signals.

Rules:

1. A transfer occurs only on `valid && ready`.
2. Producers must keep `data`, `last`, and `user` stable while `valid=1` and `ready=0`.
3. Backpressure is allowed at every stage.
4. The MVP uses bounded single-entry stage buffers or bounded FIFOs only.

## MMIO contract (`mmio_if.sv`)

The stub defines fields for spread and imbalance thresholds, risk limits, a hard override input, model and policy select, and counter readback. MVP control inputs are exposed directly on `apu_top` while the interface shape stays stable for later expansion.
