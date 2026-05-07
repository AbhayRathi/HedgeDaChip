module decision_pipe (
  input  logic                               clk,
  input  logic                               rst,
  input  logic signed [31:0]                 spread_threshold,
  input  logic signed [31:0]                 imbalance_threshold,
  input  logic                               in_valid,
  output logic                               in_ready,
  input  logic [$bits(apu_types::feature_t)-1:0] in_feature_data,
  output logic                               out_valid,
  input  logic                               out_ready,
  output logic [$bits(apu_types::action_t)-1:0]  out_action_data
);
  import apu_types::*;

  feature_t stage0_feature;
  feature_t stage1_feature;
  logic stage0_valid;
  logic stage1_valid;
  action_t decided_action;
  logic pipe_advance;

  function automatic action_t decide(feature_t feature,
                                     logic signed [31:0] spread_thresh,
                                     logic signed [31:0] imbalance_thresh);
    action_t action;
    action = '0;
    action.action_type = ACTION_NONE;
    if ((feature.best_bid_qty != 32'd0) &&
        (feature.best_ask_qty != 32'd0) &&
        (feature.spread > spread_thresh)) begin
      if (feature.imbalance >= imbalance_thresh) begin
        action.action_type = ACTION_BUY;
        action.price = feature.best_ask_price;
        action.qty = 32'd1;
        action.reason_code = 8'd1;
      end else if (feature.imbalance <= -imbalance_thresh) begin
        action.action_type = ACTION_SELL;
        action.price = feature.best_bid_price;
        action.qty = 32'd1;
        action.reason_code = 8'd2;
      end
    end
    return action;
  endfunction

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
