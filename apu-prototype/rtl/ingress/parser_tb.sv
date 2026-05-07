module parser_tb (
  input  logic                                clk,
  input  logic                                rst,
  input  logic                                in_valid,
  output logic                                in_ready,
  input  logic [127:0]                        in_data,
  output logic                                out_valid,
  input  logic                                out_ready,
  output logic [$bits(apu_types::event_t)-1:0] out_event_data
);
  vr_if #(.W(128)) in_stream();

  assign in_stream.valid = in_valid;
  assign in_stream.data = in_data;
  assign in_stream.last = 1'b1;
  assign in_stream.user = '0;
  assign in_ready = in_stream.ready;

  parser u_parser (
    .clk(clk),
    .rst(rst),
    .in_stream(in_stream),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_event_data(out_event_data)
  );
endmodule
