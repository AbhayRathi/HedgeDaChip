module order_encoder (
  input  logic                               clk,
  input  logic                               rst,
  input  logic                               in_valid,
  output logic                               in_ready,
  input  logic [$bits(apu_types::action_t)-1:0] in_action_data,
  output logic                               out_valid,
  input  logic                               out_ready,
  output logic [127:0]                       out_data
);
  assign in_ready = !out_valid || out_ready;

  always_ff @(posedge clk) begin
    if (rst) begin
      out_valid <= 1'b0;
      out_data <= '0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        out_data <= in_action_data;
      end
    end
  end
endmodule
