module decision_pipe (
  input  logic                                   clk,
  input  logic                                   rst,
  input  logic signed [31:0]                     spread_threshold,
  input  logic signed [31:0]                     imbalance_threshold,
  input  logic                                   in_valid,
  output logic                                   in_ready,
  input  logic [$bits(apu_types::feature_t)-1:0] in_feature_data,
  output logic                                   out_valid,
  input  logic                                   out_ready,
  output logic [$bits(apu_types::action_t)-1:0]  out_action_data
);
  import apu_params::*;
  import apu_types::*;
  localparam int PIPE_STAGES = DECISION_PIPE_STAGES;

  feature_t stage0_feature;
  feature_t stage1_feature;
  logic stage0_valid;
  logic stage1_valid;
  action_t decided_action;
  logic pipe_advance;

  function automatic logic [31:0] abs_imbalance(input logic signed [31:0] value);
    logic signed [31:0] positive;
    begin
      positive = (value < 0) ? -value : value;
      return positive[31:0];
    end
  endfunction

  function automatic logic [31:0] clamp_qty(input logic [63:0] raw_qty);
    logic [31:0] limited_qty;
    begin
      limited_qty = raw_qty[31:0];
      if (raw_qty < 64'(MIN_QTY)) begin
        limited_qty = MIN_QTY;
      end else if (raw_qty > 64'(MAX_QTY)) begin
        limited_qty = MAX_QTY;
      end
      return limited_qty;
    end
  endfunction

  function automatic logic [31:0] compute_qty(input logic signed [31:0] spread,
                                              input logic signed [31:0] imbalance,
                                              input logic signed [31:0] imbalance_thresh);
    logic [31:0] spread_scale;
    logic [31:0] imbalance_mag;
    logic [31:0] threshold_mag;
    logic [63:0] imbalance_ratio;
    logic [63:0] raw_qty;
    begin
      spread_scale = (spread > 32'sd0) ? spread[31:0] : 32'd1;
      imbalance_mag = abs_imbalance(imbalance);
      threshold_mag = abs_imbalance(imbalance_thresh);
      if (imbalance_mag < threshold_mag) begin
        imbalance_ratio = 64'd0;
      end else begin
        imbalance_ratio = 64'(imbalance_mag) / 64'(spread_scale);
      end
      raw_qty = imbalance_ratio * BASE_QTY;
      return clamp_qty(raw_qty);
    end
  endfunction

  /* verilator lint_off UNUSEDSIGNAL */
  function automatic action_t decide(feature_t feature,
                                     logic signed [31:0] spread_thresh,
                                     logic signed [31:0] imbalance_thresh);
    action_t action;
    begin
      action = '0;
      action.action_type = ACTION_NONE;
      action.timestamp = feature.event_ts;
      if ((feature.best_bid_qty != 32'd0) &&
          (feature.best_ask_qty != 32'd0) &&
          (feature.spread > spread_thresh)) begin
        if (feature.imbalance >= imbalance_thresh) begin
          action.action_type = ACTION_BUY;
          action.price = feature.best_ask_price;
          action.qty = compute_qty(feature.spread, feature.imbalance, imbalance_thresh);
          action.reason_code = 8'd1;
        end else if (feature.imbalance <= -imbalance_thresh) begin
          action.action_type = ACTION_SELL;
          action.price = feature.best_bid_price;
          action.qty = compute_qty(feature.spread, feature.imbalance, imbalance_thresh);
          action.reason_code = 8'd2;
        end
      end
      return action;
    end
  endfunction
  /* verilator lint_on UNUSEDSIGNAL */

  initial begin
    if (PIPE_STAGES != 3) begin
      $error("decision_pipe currently supports exactly 3 stages");
    end
  end

  assign pipe_advance = !out_valid || out_ready;
  assign in_ready = pipe_advance;
  assign decided_action = decide(stage1_feature, spread_threshold, imbalance_threshold);

  always_ff @(posedge clk) begin
    if (rst) begin
      stage0_valid <= 1'b0;
      stage1_valid <= 1'b0;
      out_valid <= 1'b0;
      stage0_feature <= '0;
      stage1_feature <= '0;
      out_action_data <= '0;
    end else if (pipe_advance) begin
      out_valid <= stage1_valid;
      if (stage1_valid) begin
        out_action_data <= decided_action;
      end
      stage1_valid <= stage0_valid;
      if (stage0_valid) begin
        stage1_feature <= stage0_feature;
      end
      stage0_valid <= in_valid;
      if (in_valid) begin
        stage0_feature <= feature_t'(in_feature_data);
      end
    end
  end
endmodule
