module stream_rx (
  input  logic         clk,
  input  logic         rst,
  input  logic         stamp_ts,
  input  logic [31:0]  now_ts,
  input  logic         in_valid,
  output logic         in_ready,
  input  logic [127:0] in_data,
  output logic         out_valid,
  input  logic         out_ready,
  output logic [127:0] out_data
);
  logic [127:0] stamped_data;

  always_comb begin
    stamped_data = in_data;
    if (stamp_ts && (in_data[104:73] == 32'd0)) begin
      stamped_data[104:73] = now_ts;
    end
  end

  assign in_ready = !out_valid || out_ready;

  always_ff @(posedge clk) begin
    if (rst) begin
      out_valid <= 1'b0;
      out_data <= '0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        out_data <= stamped_data;
      end
    end
  end
endmodule
