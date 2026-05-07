# Coding standards

- Use `always_ff` for sequential logic and `always_comb` for combinational logic.
- Avoid inferred latches.
- Use synchronous active-high reset in the MVP.
- Parameterize widths and depths.
- Every module should describe purpose, interface, latency, and backpressure behavior in comments.
- Favor simple deterministic pipelines over variable-latency logic.
