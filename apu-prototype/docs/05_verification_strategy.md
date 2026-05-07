# Verification strategy

The Python golden model in `sw_golden/models.py` is the functional source of truth for supported MVP behaviors.

## Required checks

- parser field extraction and invalid-event handling
- orderbook / feature generation against the golden model
- exact decision output matching against the golden model
- risk gating invariants (hard override, sanity checks, deterministic rate limiting)
- end-to-end replay equivalence and latency-bound checks
- determinism: repeated replay with the same traffic and ready pattern yields identical outputs and cycle offsets
