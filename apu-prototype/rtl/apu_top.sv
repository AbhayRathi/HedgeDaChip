module apu_top (
  input  logic         clk,
  input  logic         rst,
  input  logic         kill_switch,
  input  logic         stamp_ts,
  input  logic signed [31:0] spread_threshold,
  input  logic signed [31:0] imbalance_threshold,
  input  logic [31:0]  max_orders_per_window,
  input  logic         in_valid,
  output logic         in_ready,
  input  logic [127:0] in_data,
  output logic         out_valid,
  input  logic         out_ready,
  output logic [127:0] out_data,
  output logic [31:0]  ingress_count,
  output logic [31:0]  egress_count,
  output logic [31:0]  stall_cycles
);
  import apu_types::*;

  logic [31:0] now_ts;
  logic rx_valid;
  logic rx_ready;
  logic [127:0] rx_data;
  logic parser_valid;
  logic parser_ready;
  logic [$bits(event_t)-1:0] parser_event_data;
  logic ob_valid;
  logic ob_ready;
  logic [$bits(feature_t)-1:0] ob_feature_data;
  logic decision_valid;
  logic decision_ready;
  logic [$bits(action_t)-1:0] decision_action_data;
  logic risk_valid;
  logic risk_ready;
  logic [$bits(action_t)-1:0] risk_action_data;

  timestamp u_timestamp (
    .clk(clk),
    .rst(rst),
    .now_ts(now_ts)
  );

  stream_rx u_stream_rx (
    .clk(clk),
    .rst(rst),
    .stamp_ts(stamp_ts),
    .now_ts(now_ts),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_data(in_data),
    .out_valid(rx_valid),
    .out_ready(rx_ready),
    .out_data(rx_data)
  );

  parser u_parser (
    .clk(clk),
    .rst(rst),
    .in_valid(rx_valid),
    .in_ready(rx_ready),
    .in_data(rx_data),
    .out_valid(parser_valid),
    .out_ready(parser_ready),
    .out_event_data(parser_event_data)
  );

  ob_engine u_ob_engine (
    .clk(clk),
    .rst(rst),
    .in_valid(parser_valid),
    .in_ready(parser_ready),
    .in_event_data(parser_event_data),
    .out_valid(ob_valid),
    .out_ready(ob_ready),
    .out_feature_data(ob_feature_data)
  );

  decision_pipe u_decision_pipe (
    .clk(clk),
    .rst(rst),
    .spread_threshold(spread_threshold),
    .imbalance_threshold(imbalance_threshold),
    .in_valid(ob_valid),
    .in_ready(ob_ready),
    .in_feature_data(ob_feature_data),
    .out_valid(decision_valid),
    .out_ready(decision_ready),
    .out_action_data(decision_action_data)
  );

  risk_engine u_risk_engine (
    .clk(clk),
    .rst(rst),
    .kill_switch(kill_switch),
    .max_orders_per_window(max_orders_per_window),
    .in_valid(decision_valid),
    .in_ready(decision_ready),
    .in_action_data(decision_action_data),
    .out_valid(risk_valid),
    .out_ready(risk_ready),
    .out_action_data(risk_action_data)
  );

  order_encoder u_order_encoder (
    .clk(clk),
    .rst(rst),
    .in_valid(risk_valid),
    .in_ready(risk_ready),
    .in_action_data(risk_action_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_data(out_data)
  );

  perf_counters u_perf_counters (
    .clk(clk),
    .rst(rst),
    .in_fire(in_valid && in_ready),
    .out_fire(out_valid && out_ready),
    .stall(in_valid && !in_ready),
    .in_count(ingress_count),
    .out_count(egress_count),
    .stall_cycles(stall_cycles)
  );
endmodule
