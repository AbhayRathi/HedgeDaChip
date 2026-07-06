package apu_params;
  localparam int STREAM_W = 128;
  localparam int PRICE_W = 32;
  localparam int QTY_W = 32;
  localparam int TS_W = 32;
  localparam int EVENT_FLAGS_W = 23;
  localparam int DECISION_PIPE_STAGES = 3;

  localparam logic signed [PRICE_W-1:0] DEFAULT_SPREAD_THRESHOLD = 32'sd4;
  localparam logic signed [PRICE_W-1:0] DEFAULT_IMBALANCE_THRESHOLD = 32'sd2;

  localparam int DEFAULT_MAX_ORDERS_PER_WINDOW = 4;
  localparam int DEFAULT_WINDOW_CYCLES = 16;
  localparam int DEFAULT_INGRESS_FIFO_DEPTH = 8;
  localparam int ORDERBOOK_MEM_DEPTH = 1;
  localparam int ORDERBOOK_STATE_W = PRICE_W + QTY_W;

  localparam logic [QTY_W-1:0] BASE_QTY = 32'd4;
  localparam logic [QTY_W-1:0] MIN_QTY = 32'd1;
  localparam logic [QTY_W-1:0] MAX_QTY = 32'd16;
endpackage
