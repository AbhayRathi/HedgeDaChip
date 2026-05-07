# Definition of done

A module or integration milestone is considered done only when every item below has an identified verifier and an explicit validation path.

## 1. Unit behavior is proven

- **What must be true:** the module passes a focused cocotb unit test that exercises its nominal path and at least one edge case.
- **Who verifies it:** the contributor implementing the change, then CI on every push.
- **How it is verified:** a dedicated `tb/test_*.py` test must pass locally and in GitHub Actions.

## 2. Golden-model agreement exists where applicable

- **What must be true:** externally visible behavior matches the Python source-of-truth model.
- **Who verifies it:** the contributor through local regression and reviewers through the committed test logic.
- **How it is verified:** tests use `GoldenComparator` so any mismatch report names the field and triggering input event.

## 3. Latency and backpressure behavior are documented

- **What must be true:** the stage describes its pipeline depth, handshake behavior, and any bounded stall conditions.
- **Who verifies it:** the contributor updates docs; reviewers confirm the description matches the RTL.
- **How it is verified:** docs and module-level comments are inspected during review, and latency-sensitive tests must assert cycle bounds where relevant.

## 4. Safety or invariants are covered

- **What must be true:** any invariant claimed by the module has a regression test.
- **Who verifies it:** the contributor and CI.
- **How it is verified:** examples include kill-switch precedence, deterministic invalid-frame handling, bounded FIFO behavior, and checksum correctness.

## 5. Integration is proven for pipeline-visible blocks

- **What must be true:** if the block participates in `apu_top`, an end-to-end regression must observe its behavior in-context.
- **Who verifies it:** the contributor first, then reviewers by reading the integrated test and CI logs.
- **How it is verified:** `test_end2end.py`, lint, and the CI workflow must all pass.

## 6. Tooling and docs stay in sync

- **What must be true:** any new parameter, interface contract, or output format is reflected in the golden model, tests, and documentation.
- **Who verifies it:** the contributor during implementation and reviewers during final inspection.
- **How it is verified:** shared constants live in both RTL and Python, and docs are checked for completeness in CI.
