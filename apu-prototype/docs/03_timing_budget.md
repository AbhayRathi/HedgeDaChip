# Timing budget

Deterministic means bounded worst-case latency in cycles under all supported traffic, including bursts and downstream backpressure.

| Module | Target worst-case latency |
| --- | --- |
| `stream_rx` | 0-1 cycles |
| `parser` | <= 4 cycles |
| `ob_engine` | <= 6 cycles |
| `decision_pipe` | fixed 3-register pipeline |
| `risk_engine` | <= 2 cycles |
| `order_encoder` | <= 2 cycles |
| **Total reflex path target** | **<= 20 cycles** |

## Stall behavior

All modules use bounded buffering only. When downstream deasserts `ready`, the upstream-facing `ready` deasserts and the module holds the current payload stable until accepted.
