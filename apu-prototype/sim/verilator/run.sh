#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
verilator --lint-only --Wall --sv -Wno-MULTITOP \
  rtl/pkg/apu_params.sv rtl/pkg/apu_types.sv rtl/ifc/vr_if.sv rtl/ifc/mmio_if.sv \
  rtl/util/fifo.sv rtl/util/timestamp.sv rtl/util/perf_counters.sv \
  rtl/ingress/stream_rx.sv rtl/ingress/parser.sv rtl/ingress/eth_rx_stub.sv \
  rtl/state/ob_mem.sv rtl/state/pim_prims.sv rtl/state/ob_engine.sv \
  rtl/deterministic/decision_pipe.sv rtl/risk/risk_engine.sv rtl/egress/order_encoder.sv rtl/apu_top.sv
make -C sim/verilator
