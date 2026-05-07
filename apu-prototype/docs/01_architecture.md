# Architecture

## MVP v1 data path

```text
host replay stream
  -> stream_rx
  -> parser
  -> ob_engine
  -> decision_pipe
  -> risk_engine
  -> order_encoder
  -> host-visible action stream
```

The design implements a single-clock reflex path with bounded buffering and valid/ready flow control at every stage. `risk_engine` is the final authority and can block every candidate action via hard override, sanity checks, and a deterministic rate limiter.

## Future-facing boundaries

- `eth_rx_stub.sv`: placeholder for NIC ingest
- `mmio_if.sv`: future control plane interface
- `pim_prims.sv`: stable API for memory-adjacent compute expansion
- `fpga/`: placeholder for vendor build collateral
