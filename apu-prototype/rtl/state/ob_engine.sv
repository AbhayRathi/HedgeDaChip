module ob_engine (
  input  logic                              clk,
  input  logic                              rst,
  input  logic                              in_valid,
  output logic                              in_ready,
  input  logic [$bits(apu_types::event_t)-1:0]   in_event_data,
  output logic                              out_valid,
  input  logic                              out_ready,
  output logic [$bits(apu_types::feature_t)-1:0] out_feature_data
);
  import apu_types::*;

  event_t in_event;
  feature_t next_feature;
  logic signed [31:0] best_bid_price_r;
  logic [31:0] best_bid_qty_r;
  logic signed [31:0] best_ask_price_r;
  logic [31:0] best_ask_qty_r;
  logic signed [31:0] last_trade_price_r;
  logic [31:0] last_trade_qty_r;
  logic signed [31:0] best_bid_price_n;
  logic [31:0] best_bid_qty_n;
  logic signed [31:0] best_ask_price_n;
  logic [31:0] best_ask_qty_n;
  logic signed [31:0] last_trade_price_n;
  logic [31:0] last_trade_qty_n;
  logic signed [31:0] spread_n;
  logic signed [31:0] imbalance_n;

  assign in_event = event_t'(in_event_data);
  assign in_ready = !out_valid || out_ready;

  always_comb begin
    best_bid_price_n = best_bid_price_r;
    best_bid_qty_n = best_bid_qty_r;
    best_ask_price_n = best_ask_price_r;
    best_ask_qty_n = best_ask_qty_r;
    last_trade_price_n = last_trade_price_r;
    last_trade_qty_n = last_trade_qty_r;

    unique case (in_event.event_type)
      EVENT_ADD, EVENT_UPDATE: begin
        if (!in_event.side) begin
          if ((best_bid_qty_r == 32'd0) || (in_event.price > best_bid_price_r) || (in_event.price == best_bid_price_r)) begin
            best_bid_price_n = in_event.price;
            best_bid_qty_n = in_event.qty;
          end
        end else begin
          if ((best_ask_qty_r == 32'd0) || (in_event.price < best_ask_price_r) || (in_event.price == best_ask_price_r)) begin
            best_ask_price_n = in_event.price;
            best_ask_qty_n = in_event.qty;
          end
        end
      end
      EVENT_CANCEL, EVENT_TRADE: begin
        if (!in_event.side && (in_event.price == best_bid_price_r)) begin
          if (in_event.qty >= best_bid_qty_r) begin
            best_bid_qty_n = 32'd0;
            best_bid_price_n = 32'sd0;
          end else begin
            best_bid_qty_n = best_bid_qty_r - in_event.qty;
          end
        end
        if (in_event.side && (in_event.price == best_ask_price_r)) begin
          if (in_event.qty >= best_ask_qty_r) begin
            best_ask_qty_n = 32'd0;
            best_ask_price_n = 32'sd0;
          end else begin
            best_ask_qty_n = best_ask_qty_r - in_event.qty;
          end
        end
        if (in_event.event_type == EVENT_TRADE) begin
          last_trade_price_n = in_event.price;
          last_trade_qty_n = in_event.qty;
        end
      end
      default: begin
      end
    endcase

    if ((best_bid_qty_n != 32'd0) && (best_ask_qty_n != 32'd0) && (best_ask_price_n >= best_bid_price_n)) begin
      spread_n = best_ask_price_n - best_bid_price_n;
    end else begin
      spread_n = 32'sd0;
    end
    imbalance_n = $signed(best_bid_qty_n) - $signed(best_ask_qty_n);

    next_feature = '0;
    next_feature.best_bid_price = best_bid_price_n;
    next_feature.best_bid_qty = best_bid_qty_n;
    next_feature.best_ask_price = best_ask_price_n;
    next_feature.best_ask_qty = best_ask_qty_n;
    next_feature.spread = spread_n;
    next_feature.imbalance = imbalance_n;
    next_feature.last_trade_price = last_trade_price_n;
    next_feature.last_trade_qty = last_trade_qty_n;
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      best_bid_price_r <= '0;
      best_bid_qty_r <= '0;
      best_ask_price_r <= '0;
      best_ask_qty_r <= '0;
      last_trade_price_r <= '0;
      last_trade_qty_r <= '0;
      out_valid <= 1'b0;
      out_feature_data <= '0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        best_bid_price_r <= best_bid_price_n;
        best_bid_qty_r <= best_bid_qty_n;
        best_ask_price_r <= best_ask_price_n;
        best_ask_qty_r <= best_ask_qty_n;
        last_trade_price_r <= last_trade_price_n;
        last_trade_qty_r <= last_trade_qty_n;
        out_feature_data <= next_feature;
      end
    end
  end
endmodule
