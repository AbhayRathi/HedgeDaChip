module perf_counters (
  input  logic        clk,
  input  logic        rst,
  input  logic        in_fire,
  input  logic        out_fire,
  input  logic        stall,
  output logic [31:0] in_count,
  output logic [31:0] out_count,
  output logic [31:0] stall_cycles
);
  always_ff @(posedge clk) begin
    if (rst) begin
      in_count <= '0;
      out_count <= '0;
      stall_cycles <= '0;
    end else begin
      if (in_fire) begin
        in_count <= in_count + 1'b1;
      end
      if (out_fire) begin
        out_count <= out_count + 1'b1;
      end
      if (stall) begin
        stall_cycles <= stall_cycles + 1'b1;
      end
    end
  end
endmodule
