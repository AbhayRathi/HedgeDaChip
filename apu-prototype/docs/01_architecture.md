# Architecture

## MVP v1 reflex path

The current FPGA-first MVP implements a single-clock deterministic reflex path with one explicit elastic buffer and one memory-backed top-of-book stage. The data path is intentionally simple so that latency can be budgeted in cycles and each stage can be replaced later without changing the contract-first stream boundaries.

```text
host replay
  |
  v
+-----------+    +-------------+    +--------------+    +------------+
| stream_rx | -> | ingress FIFO | -> | parser(vr_if)| -> | ob_engine  |
|   0-1 cyc |    |   0-8 beats  |    |   <= 1 cyc   |    |  BRAM +    |
| stamps ts |    | bounded      |    | frame decode |    | PIM helpers|
+-----------+    +-------------+    +--------------+    +------------+
                                                                 |
                                                                 | <= 2 cyc
                                                                 v
                                                          +-------------+
                                                          | decision    |
                                                          | fixed 3 regs|
                                                          +-------------+
                                                                 |
                                                                 | <= 1 cyc
                                                                 v
                                                          +-------------+
                                                          | risk_engine |
                                                          | hard gate   |
                                                          +-------------+
                                                                 |
                                                                 | <= 1 cyc
                                                                 v
                                                          +-------------+
                                                          |order_encoder|
                                                          |128b egress  |
                                                          +-------------+
                                                                 |
                                                                 v
                                                          host-visible actions
```

## Stage responsibilities

- **`stream_rx`** accepts the host replay stream, applies valid/ready backpressure, and optionally stamps timestamps into replay frames that omit them.
- **`fifo`** demonstrates bounded elastic buffering at ingress. It absorbs short host bursts and gives the downstream parser a stable stream contract.
- **`parser`** is the first live use of `vr_if`. It decodes a 128-bit frame into `event_t` and normalizes invalid event types into deterministic `NOP + error-flag` behavior.
- **`ob_engine`** demonstrates the memory-centric principle. Best bid and best ask state are now stored in `ob_mem` instances rather than plain registers, and the stage absorbs the one-cycle BRAM read latency before emitting `feature_t`.
- **`decision_pipe`** is a fixed three-register pipeline. It computes spread and imbalance triggers, then sizes actions from a bounded quantity formula using the shared APU parameters.
- **`risk_engine`** is the final authority. Kill switch, sanity checks, and rate limiting can only block actions; no later stage can re-enable one.
- **`order_encoder`** emits a concrete 128-bit host wire format with action, price, quantity, reason code, timestamp, and checksum.

## Latency and determinism notes

The deterministic contract is enforced with bounded resources only: one ingress FIFO, one synchronous BRAM read in the orderbook stage, and single-register handshake boundaries elsewhere. The worst-case latency remains bounded under bursts because the FIFO depth is fixed, the orderbook accepts at a deterministic cadence that matches the BRAM latency, and no stage contains an unbounded loop or search.

## Future abstraction boundaries

- `pim_prims.sv` is the abstraction boundary for future memory-adjacent compute or CIM replacement. The MVP uses ordinary logic implementations today, but `ob_engine` already calls the package functions instead of inlining comparison policy.
- `mmio_if.sv` reserves the control-plane contract needed for later policy and model updates.
- `eth_rx_stub.sv` marks the future NIC ingest replacement point.
- `fpga/` holds the board-facing collateral needed to move from simulation to implementation.
