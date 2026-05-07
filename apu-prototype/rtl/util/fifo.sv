module fifo #(
  parameter int WIDTH = 128,
  parameter int DEPTH = 4,
  localparam int PTR_W = (DEPTH <= 1) ? 1 : $clog2(DEPTH)
) (
  input  logic             clk,
  input  logic             rst,
  input  logic             s_valid,
  output logic             s_ready,
  input  logic [WIDTH-1:0] s_data,
  output logic             m_valid,
  input  logic             m_ready,
  output logic [WIDTH-1:0] m_data,
  output logic [PTR_W:0]   occupancy
);
  logic [WIDTH-1:0] mem [0:DEPTH-1];
  logic [PTR_W-1:0] wr_ptr;
  logic [PTR_W-1:0] rd_ptr;
  logic [PTR_W:0]   count;
  localparam logic [PTR_W:0] DEPTH_COUNT = (PTR_W + 1)'(DEPTH);
  localparam logic [PTR_W-1:0] LAST_PTR = PTR_W'(DEPTH - 1);
  logic push;
  logic pop;

  assign s_ready = (count < DEPTH_COUNT);
  assign m_valid = (count != 0);
  assign m_data = mem[rd_ptr];
  assign occupancy = count;
  assign push = s_valid && s_ready;
  assign pop = m_valid && m_ready;

  always_ff @(posedge clk) begin
    if (rst) begin
      wr_ptr <= '0;
      rd_ptr <= '0;
      count <= '0;
    end else begin
      if (push) begin
        mem[wr_ptr] <= s_data;
        if (wr_ptr == LAST_PTR) begin
          wr_ptr <= '0;
        end else begin
          wr_ptr <= wr_ptr + 1'b1;
        end
      end
      if (pop) begin
        if (rd_ptr == LAST_PTR) begin
          rd_ptr <= '0;
        end else begin
          rd_ptr <= rd_ptr + 1'b1;
        end
      end
      case ({push, pop})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule
