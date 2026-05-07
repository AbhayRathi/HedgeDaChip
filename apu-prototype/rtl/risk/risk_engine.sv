module risk_engine #(
  parameter int WINDOW_CYCLES = apu_params::DEFAULT_WINDOW_CYCLES
) (
  input  logic                                  clk,
  input  logic                                  rst,
  input  logic                                  kill_switch,
  input  logic [31:0]                           max_orders_per_window,
  input  logic                                  in_valid,
  output logic                                  in_ready,
  input  logic [$bits(apu_types::action_t)-1:0]  in_action_data,
  output logic                                  out_valid,
  input  logic                                  out_ready,
  output logic [$bits(apu_types::action_t)-1:0] out_action_data
);
  import apu_params::*;
  import apu_types::*;

  localparam logic [7:0] REASON_KILL = 8'h10;
  localparam logic [7:0] REASON_QTY = 8'h11;
  localparam logic [7:0] REASON_PRICE = 8'h12;
  localparam logic [7:0] REASON_RATE = 8'h13;
  localparam int WINDOW_W = (WINDOW_CYCLES <= 1) ? 1 : $clog2(WINDOW_CYCLES);

  logic [31:0] orders_in_window;
  logic [WINDOW_W-1:0] window_counter;
  logic window_wrap;
  action_t candidate_action;
  action_t gated_action;
  logic [31:0] effective_orders;
  logic [31:0] configured_limit;

  assign candidate_action = action_t'(in_action_data);
  assign in_ready = !out_valid || out_ready;
  assign window_wrap = (window_counter == WINDOW_W'(WINDOW_CYCLES - 1));
  assign effective_orders = window_wrap ? 32'd0 : orders_in_window;
  assign configured_limit = (max_orders_per_window == 32'd0) ? DEFAULT_MAX_ORDERS_PER_WINDOW : max_orders_per_window;

  always_comb begin
    gated_action = candidate_action;
    if (candidate_action.action_type != ACTION_NONE) begin
      if (kill_switch) begin
        gated_action = '0;
        gated_action.timestamp = candidate_action.timestamp;
        gated_action.reason_code = REASON_KILL;
      end else if (candidate_action.qty == 32'd0) begin
        gated_action = '0;
        gated_action.timestamp = candidate_action.timestamp;
        gated_action.reason_code = REASON_QTY;
      end else if (candidate_action.price == 32'sd0) begin
        gated_action = '0;
        gated_action.timestamp = candidate_action.timestamp;
        gated_action.reason_code = REASON_PRICE;
      end else if (effective_orders >= configured_limit) begin
        gated_action = '0;
        gated_action.timestamp = candidate_action.timestamp;
        gated_action.reason_code = REASON_RATE;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      orders_in_window <= '0;
      window_counter <= '0;
      out_valid <= 1'b0;
      out_action_data <= '0;
    end else begin
      if (window_wrap) begin
        window_counter <= '0;
        orders_in_window <= '0;
      end else begin
        window_counter <= window_counter + 1'b1;
      end
      if (in_ready) begin
        out_valid <= in_valid;
        if (in_valid) begin
          out_action_data <= gated_action;
          if ((candidate_action.action_type != ACTION_NONE) && (gated_action.action_type != ACTION_NONE)) begin
            orders_in_window <= effective_orders + 1'b1;
          end
        end
      end
    end
  end
endmodule
