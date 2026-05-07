ROOT := $(abspath $(CURDIR)/../..)
BUILD_DIR := $(CURDIR)/build
OBJ_DIR := $(BUILD_DIR)/obj_dir
BINARY := $(BUILD_DIR)/apu_top_smoke
SOURCES := \
	$(ROOT)/rtl/pkg/apu_params.sv \
	$(ROOT)/rtl/pkg/apu_types.sv \
	$(ROOT)/rtl/ifc/vr_if.sv \
	$(ROOT)/rtl/ifc/mmio_if.sv \
	$(ROOT)/rtl/util/fifo.sv \
	$(ROOT)/rtl/util/timestamp.sv \
	$(ROOT)/rtl/util/perf_counters.sv \
	$(ROOT)/rtl/ingress/stream_rx.sv \
	$(ROOT)/rtl/ingress/parser.sv \
	$(ROOT)/rtl/ingress/eth_rx_stub.sv \
	$(ROOT)/rtl/state/ob_mem.sv \
	$(ROOT)/rtl/state/pim_prims.sv \
	$(ROOT)/rtl/state/ob_engine.sv \
	$(ROOT)/rtl/deterministic/decision_pipe.sv \
	$(ROOT)/rtl/risk/risk_engine.sv \
	$(ROOT)/rtl/egress/order_encoder.sv \
	$(ROOT)/rtl/apu_top.sv

.PHONY: all clean

all: $(BINARY)

$(BINARY): $(SOURCES)
	mkdir -p $(BUILD_DIR)
	verilator --binary --sv --top-module apu_top --Mdir $(OBJ_DIR) $(SOURCES) -o apu_top_smoke
	cp $(OBJ_DIR)/apu_top_smoke $(BINARY)

clean:
	rm -rf $(BUILD_DIR)
