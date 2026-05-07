# Verification strategy

The verification flow is built around a single rule: the Python golden model in `sw_golden/models.py` is the functional source of truth for every behavior the RTL claims to support. A cocotb test is only complete when it can explain a divergence in terms of an input event, an expected field, and the actual field observed in simulation.

## Golden model contract

The golden model provides four core contracts:

1. **Replay-frame parsing** via `parse_event_frame()`.
2. **Orderbook state evolution** via `OrderBookModel.apply()`.
3. **Decision generation** via `decision_model()` and the shared quantity-sizing formula.
4. **Risk gating and output framing** via `RiskModel`, `encode_output_frame()`, and `decode_output_frame()`.

Shared constants in `sw_golden/apu_params.py` mirror the RTL package values used by the reflex path so tests do not drift away from the implementation defaults.

## Test coverage by file

- **`test_parser.py`** checks parser field extraction, invalid-event normalization, and output stability under backpressure.
- **`test_orderbook.py`** checks the BRAM-backed orderbook path against the golden model and explicitly asserts the added latency caused by synchronous memory reads.
- **`test_decision.py`** checks action generation and verifies the quantity formula across minimum, nominal, and saturation cases.
- **`test_risk.py`** checks kill-switch behavior, sanity filtering, and deterministic rate limiting.
- **`test_end2end.py`** checks the full reflex path, verifies decoded output frames against the golden model, measures latency bounds, and demonstrates that the ingress FIFO absorbs a burst without dropping events.
- **`test_fifo.py`**, **`test_stream_rx.py`**, and **`test_perf_counters.py`** provide focused unit coverage for utility blocks that are also used by the integrated path.

## Comparator strategy

`sw_golden/compare.py` now exposes `GoldenComparator`, which compares fields one-by-one and returns a structured report. On failure, the report includes the event index, field name, expected value, actual value, and the replay input that triggered the mismatch.

## Adding a new test

When adding a new RTL feature:

1. add or extend the matching golden-model behavior first;
2. encode the same constants in `sw_golden/apu_params.py` when a new RTL parameter becomes part of the contract;
3. create a focused cocotb test that isolates the new behavior before relying on end-to-end coverage;
4. use `GoldenComparator` for all field-level assertions so failures remain actionable;
5. enable wave output for the new test so CI can upload traces on failure.

## Expected validation commands

From `apu-prototype/`:

- `./sim/verilator/run.sh` for lint plus smoke build
- `./sim/cocotb/run.sh` for cocotb regression
- `pytest --cov=sw_golden --cov-report=term-missing --cov-fail-under=80 tb/` for the golden-model coverage gate
