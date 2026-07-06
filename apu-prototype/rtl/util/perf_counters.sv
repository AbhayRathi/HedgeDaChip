module perf_counters #(
  parameter int COUNTER_W = 32,
  parameter int OCCUPANCY_W = 4
) (
  input  logic                   clk,
  input  logic                   rst,
  input  logic                   in_fire,
  input  logic                   out_fire,
  input  logic                   stall,
  input  logic [OCCUPANCY_W-1:0] occupancy,
  output logic [COUNTER_W-1:0]   in_count,
  output logic [COUNTER_W-1:0]   out_count,
  output logic [COUNTER_W-1:0]   stall_cycles,
  output logic [COUNTER_W-1:0]   max_occupancy
);
  logic [COUNTER_W-1:0] occupancy_ext;

  assign occupancy_ext = COUNTER_W'(occupancy);

  always_ff @(posedge clk) begin
    if (rst) begin
      in_count <= '0;
      out_count <= '0;
      stall_cycles <= '0;
      max_occupancy <= '0;
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
      if (occupancy_ext > max_occupancy) begin
        max_occupancy <= occupancy_ext;
      end
    end
  end
endmodule
