package apu_params;
  localparam int STREAM_W = 128;
  localparam int PRICE_W = 32;
  localparam int QTY_W = 32;
  localparam int TS_W = 32;
  localparam int EVENT_FLAGS_W = 23;
  localparam int DECISION_PIPE_STAGES = 3;
  localparam logic signed [31:0] DEFAULT_SPREAD_THRESHOLD = 32'sd4;
  localparam logic signed [31:0] DEFAULT_IMBALANCE_THRESHOLD = 32'sd1;
  localparam int DEFAULT_MAX_ORDERS_PER_WINDOW = 4;
  localparam int DEFAULT_WINDOW_CYCLES = 16;
endpackage
