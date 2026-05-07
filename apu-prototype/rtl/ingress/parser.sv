module parser (
  input  logic                           clk,
  input  logic                           rst,
  input  logic                           in_valid,
  output logic                           in_ready,
  input  logic [127:0]                   in_data,
  output logic                           out_valid,
  input  logic                           out_ready,
  output logic [$bits(apu_types::event_t)-1:0] out_event_data
);
  import apu_types::*;

  event_t parsed_event;
  logic valid_event_type;

  assign valid_event_type = (in_data[7:0] <= EVENT_UPDATE);
  assign in_ready = !out_valid || out_ready;

  always_comb begin
    parsed_event = '0;
    parsed_event.event_type = valid_event_type ? in_data[7:0] : EVENT_NOP;
    parsed_event.side = in_data[8];
    parsed_event.price = in_data[40:9];
    parsed_event.qty = in_data[72:41];
    parsed_event.ts = in_data[104:73];
    parsed_event.flags = in_data[127:105];
    if (!valid_event_type) begin
      parsed_event.flags[0] = 1'b1;
    end
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      out_valid <= 1'b0;
      out_event_data <= '0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        out_event_data <= parsed_event;
      end
    end
  end
endmodule
