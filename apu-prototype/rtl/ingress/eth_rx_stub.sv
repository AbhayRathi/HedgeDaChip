module eth_rx_stub (
  input  logic clk,
  input  logic rst,
  output logic idle
);
  always_ff @(posedge clk) begin
    if (rst) begin
      idle <= 1'b1;
    end else begin
      idle <= 1'b1;
    end
  end
endmodule
