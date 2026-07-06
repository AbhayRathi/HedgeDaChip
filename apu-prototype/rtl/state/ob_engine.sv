module ob_engine (
  input  logic                                  clk,
  input  logic                                  rst,
  input  logic                                  in_valid,
  output logic                                  in_ready,
  input  logic [$bits(apu_types::event_t)-1:0]   in_event_data,
  output logic                                  out_valid,
  input  logic                                  out_ready,
  output logic [$bits(apu_types::feature_t)-1:0] out_feature_data
);
  import apu_params::*;
  import apu_types::*;
  import pim_prims::*;

  localparam int MEM_ADDR_W = (ORDERBOOK_MEM_DEPTH <= 1) ? 1 : $clog2(ORDERBOOK_MEM_DEPTH);

  event_t in_event;
  feature_t response_feature_n;
  feature_t response_feature_r;

  logic [MEM_ADDR_W-1:0] state_addr;
  logic [ORDERBOOK_STATE_W-1:0] bid_rdata;
  logic [ORDERBOOK_STATE_W-1:0] ask_rdata;
  logic [ORDERBOOK_STATE_W-1:0] bid_wdata;
  logic [ORDERBOOK_STATE_W-1:0] ask_wdata;
  logic bid_we;
  logic ask_we;

  logic signed [31:0] best_bid_price_q;
  logic [31:0] best_bid_qty_q;
  logic signed [31:0] best_ask_price_q;
  logic [31:0] best_ask_qty_q;
  logic signed [31:0] best_bid_price_n;
  logic [31:0] best_bid_qty_n;
  logic signed [31:0] best_ask_price_n;
  logic [31:0] best_ask_qty_n;
  logic signed [31:0] last_trade_price_r;
  logic [31:0] last_trade_qty_r;
  logic signed [31:0] last_trade_price_n;
  logic [31:0] last_trade_qty_n;
  logic signed [31:0] spread_n;
  logic signed [31:0] imbalance_n;
  typedef enum logic [1:0] {
    ST_INIT_WRITE,
    ST_INIT_PRIME,
    ST_IDLE,
    ST_RESPOND
  } state_e;
  state_e state_r;
  logic accept_input;
  logic output_slot_available;
  logic event_has_error;

  assign in_event = event_t'(in_event_data);
  assign state_addr = '0;
  assign best_bid_price_q = $signed(bid_rdata[31:0]);
  assign best_bid_qty_q = bid_rdata[63:32];
  assign best_ask_price_q = $signed(ask_rdata[31:0]);
  assign best_ask_qty_q = ask_rdata[63:32];
  assign output_slot_available = !out_valid || out_ready;
  assign in_ready = (state_r == ST_IDLE) && output_slot_available;
  assign accept_input = in_valid && in_ready;
  assign event_has_error = in_event.flags[0];

  ob_mem #(
    .WIDTH(ORDERBOOK_STATE_W),
    .DEPTH(ORDERBOOK_MEM_DEPTH)
  ) u_bid_mem (
    .clk(clk),
    .we(bid_we),
    .waddr(state_addr),
    .wdata(bid_wdata),
    .raddr(state_addr),
    .rdata(bid_rdata)
  );

  ob_mem #(
    .WIDTH(ORDERBOOK_STATE_W),
    .DEPTH(ORDERBOOK_MEM_DEPTH)
  ) u_ask_mem (
    .clk(clk),
    .we(ask_we),
    .waddr(state_addr),
    .wdata(ask_wdata),
    .raddr(state_addr),
    .rdata(ask_rdata)
  );

  always_comb begin
    best_bid_price_n = best_bid_price_q;
    best_bid_qty_n = best_bid_qty_q;
    best_ask_price_n = best_ask_price_q;
    best_ask_qty_n = best_ask_qty_q;
    last_trade_price_n = last_trade_price_r;
    last_trade_qty_n = last_trade_qty_r;

    if (accept_input) begin
      unique case (in_event.event_type)
        EVENT_ADD, EVENT_UPDATE: begin
          if (!in_event.side) begin
            if ((best_bid_qty_q == 32'd0) || cmp_price_ge(in_event.price, best_bid_price_q)) begin
              best_bid_price_n = max_price(in_event.price, best_bid_price_q);
              best_bid_qty_n = in_event.qty;
            end
          end else begin
            if ((best_ask_qty_q == 32'd0) || (min_price(in_event.price, best_ask_price_q) == in_event.price)) begin
              best_ask_price_n = min_price(in_event.price, best_ask_price_q);
              best_ask_qty_n = in_event.qty;
            end
          end
        end
        EVENT_CANCEL, EVENT_TRADE: begin
          if (!in_event.side && (in_event.price == best_bid_price_q)) begin
            if (in_event.qty >= best_bid_qty_q) begin
              best_bid_qty_n = 32'd0;
              best_bid_price_n = 32'sd0;
            end else begin
              best_bid_qty_n = best_bid_qty_q - in_event.qty;
            end
          end
          if (in_event.side && (in_event.price == best_ask_price_q)) begin
            if (in_event.qty >= best_ask_qty_q) begin
              best_ask_qty_n = 32'd0;
              best_ask_price_n = 32'sd0;
            end else begin
              best_ask_qty_n = best_ask_qty_q - in_event.qty;
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
    end

    if ((best_bid_qty_n != 32'd0) && (best_ask_qty_n != 32'd0) && cmp_price_ge(best_ask_price_n, best_bid_price_n)) begin
      spread_n = best_ask_price_n - best_bid_price_n;
    end else begin
      spread_n = 32'sd0;
    end
    imbalance_n = $signed(best_bid_qty_n) - $signed(best_ask_qty_n);

    response_feature_n = '0;
    response_feature_n.best_bid_price = best_bid_price_n;
    response_feature_n.best_bid_qty = best_bid_qty_n;
    response_feature_n.best_ask_price = best_ask_price_n;
    response_feature_n.best_ask_qty = best_ask_qty_n;
    response_feature_n.spread = spread_n;
    response_feature_n.imbalance = imbalance_n;
    response_feature_n.last_trade_price = last_trade_price_n;
    response_feature_n.last_trade_qty = last_trade_qty_n;
    response_feature_n.event_ts = in_event.ts;
    if (event_has_error) begin
      response_feature_n.event_ts = in_event.ts;
    end

    bid_we = 1'b0;
    ask_we = 1'b0;
    bid_wdata = {best_bid_qty_n, best_bid_price_n};
    ask_wdata = {best_ask_qty_n, best_ask_price_n};

    if (state_r == ST_INIT_WRITE) begin
      bid_we = 1'b1;
      ask_we = 1'b1;
      bid_wdata = '0;
      ask_wdata = '0;
    end else if (accept_input) begin
      bid_we = 1'b1;
      ask_we = 1'b1;
    end
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      state_r <= ST_INIT_WRITE;
      last_trade_price_r <= '0;
      last_trade_qty_r <= '0;
      response_feature_r <= '0;
      out_valid <= 1'b0;
      out_feature_data <= '0;
    end else begin
      if (out_valid && out_ready) begin
        out_valid <= 1'b0;
      end

      unique case (state_r)
        ST_INIT_WRITE: begin
          state_r <= ST_INIT_PRIME;
        end
        ST_INIT_PRIME: begin
          state_r <= ST_IDLE;
        end
        ST_IDLE: begin
          if (accept_input) begin
            response_feature_r <= response_feature_n;
            last_trade_price_r <= last_trade_price_n;
            last_trade_qty_r <= last_trade_qty_n;
            state_r <= ST_RESPOND;
          end
        end
        ST_RESPOND: begin
          if (output_slot_available) begin
            out_valid <= 1'b1;
            out_feature_data <= response_feature_r;
            state_r <= ST_IDLE;
          end
        end
        default: begin
          state_r <= ST_INIT_WRITE;
        end
      endcase
    end
  end
endmodule
