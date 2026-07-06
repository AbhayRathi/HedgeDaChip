module ob_mem #(
  parameter int WIDTH = 64,
  parameter int DEPTH = 16,
  localparam int ADDR_W = (DEPTH <= 1) ? 1 : $clog2(DEPTH)
) (
  input  logic              clk,
  input  logic              we,
  input  logic [ADDR_W-1:0] waddr,
  input  logic [WIDTH-1:0]  wdata,
  input  logic [ADDR_W-1:0] raddr,
  output logic [WIDTH-1:0]  rdata
);
  logic [WIDTH-1:0] mem [0:DEPTH-1];

  always_ff @(posedge clk) begin
    if (we) begin
      mem[waddr] <= wdata;
    end
    rdata <= mem[raddr];
  end
endmodule
