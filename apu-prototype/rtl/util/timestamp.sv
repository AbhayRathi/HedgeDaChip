module timestamp #(
  parameter int WIDTH = 32
) (
  input  logic             clk,
  input  logic             rst,
  output logic [WIDTH-1:0] now_ts
);
  always_ff @(posedge clk) begin
    if (rst) begin
      now_ts <= '0;
    end else begin
      now_ts <= now_ts + 1'b1;
    end
  end
endmodule
