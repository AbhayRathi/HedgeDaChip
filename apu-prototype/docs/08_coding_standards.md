# Coding standards

These standards apply to all files under `apu-prototype/` unless a later phase explicitly documents an exception.

## RTL naming conventions

- Module names use `snake_case` and match the filename.
- Registered state uses `_r` suffixes; combinational next-state values use `_n`; decoded current memory values use `_q` when they come from synchronous memory outputs.
- Stream-side handshake signals use `in_*`, `out_*`, `s_*`, or `m_*` consistently with the direction already used in the surrounding module.

## Reset style

- Use synchronous, active-high reset for MVP logic.
- Reset must leave modules in a deterministic idle state with `valid=0` and counters/registers cleared unless a documented exception exists.
- If a sub-block lacks an explicit reset port, the parent module must document and manage any warm-up or priming cycles required after reset.

## Sequential and combinational logic

- Use `always_ff` for sequential logic and `always_comb` for combinational logic.
- Avoid inferred latches by assigning sensible defaults at the top of each combinational block.
- Prefer bounded state machines or fixed-stage pipelines over variable-latency control.

## Parameters and constants

- Put cross-module constants in `rtl/pkg/apu_params.sv`.
- Use `parameter` only for caller-configurable module settings; use `localparam` for internal derived values.
- Mirror any contract-level parameter needed by tests in `sw_golden/apu_params.py`.

## Comments and documentation

- Each module should describe its purpose, interface, latency, and backpressure behavior in either module comments or the supporting docs.
- Add comments for non-obvious pipeline or memory behavior, especially when determinism depends on a warm-up cycle or a fixed stall.
- Avoid redundant comments that restate the code line-for-line.

## Python test and golden-model style

- Prefer dataclasses for typed records exchanged between tests and the golden model.
- Use `GoldenComparator` instead of raw list equality so failures remain actionable.
- Keep the Python model behaviorally aligned with the RTL rather than duplicating implementation quirks unless those quirks are part of the hardware contract.
