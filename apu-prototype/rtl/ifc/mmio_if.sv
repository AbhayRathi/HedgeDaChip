interface mmio_if;
  logic        wr_en;
  logic        rd_en;
  logic [15:0] addr;
  logic [31:0] wdata;
  logic [31:0] rdata;
  logic        ready;
endinterface
