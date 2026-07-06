package apu_types;
  import apu_params::*;
  typedef enum logic [7:0] {
    EVENT_NOP    = 8'd0,
    EVENT_ADD    = 8'd1,
    EVENT_CANCEL = 8'd2,
    EVENT_TRADE  = 8'd3,
    EVENT_UPDATE = 8'd4
  } event_type_e;

  typedef enum logic [7:0] {
    ACTION_NONE   = 8'd0,
    ACTION_BUY    = 8'd1,
    ACTION_SELL   = 8'd2,
    ACTION_CANCEL = 8'd3
  } action_type_e;

  typedef struct packed {
    logic [EVENT_FLAGS_W-1:0] flags;
    logic [TS_W-1:0] ts;
    logic [QTY_W-1:0] qty;
    logic signed [PRICE_W-1:0] price;
    logic side;
    logic [7:0] event_type;
  } event_t;

  typedef struct packed {
    logic [TS_W-1:0] event_ts;
    logic [QTY_W-1:0] last_trade_qty;
    logic signed [PRICE_W-1:0] last_trade_price;
    logic signed [PRICE_W-1:0] imbalance;
    logic signed [PRICE_W-1:0] spread;
    logic [QTY_W-1:0] best_ask_qty;
    logic signed [PRICE_W-1:0] best_ask_price;
    logic [QTY_W-1:0] best_bid_qty;
    logic signed [PRICE_W-1:0] best_bid_price;
  } feature_t;

  typedef struct packed {
    logic [15:0] reserved;
    logic [TS_W-1:0] timestamp;
    logic [7:0] reason_code;
    logic [QTY_W-1:0] qty;
    logic signed [PRICE_W-1:0] price;
    logic [7:0] action_type;
  } action_t;
endpackage
