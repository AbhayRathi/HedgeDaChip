module order_encoder (
  input  logic                                  clk,
  input  logic                                  rst,
  input  logic [31:0]                           now_ts,
  input  logic                                  in_valid,
  output logic                                  in_ready,
  input  logic [$bits(apu_types::action_t)-1:0]  in_action_data,
  output logic                                  out_valid,
  input  logic                                  out_ready,
  output logic [127:0]                          out_data
);
  import apu_types::*;

  /* verilator lint_off UNUSEDSIGNAL */
  action_t action;
  /* verilator lint_on UNUSEDSIGNAL */
  logic [127:0] encoded_frame;

  function automatic logic [7:0] output_reason_code(input logic [7:0] action_type,
                                                    input logic [7:0] reason_code);
    begin
      if (action_type == ACTION_BUY) begin
        return 8'd1;
      end
      if (action_type == ACTION_SELL) begin
        return 8'd2;
      end
      if (reason_code != 8'd0) begin
        return 8'd3;
      end
      return 8'd0;
    end
  endfunction

  function automatic logic [15:0] checksum16(input logic [127:0] frame_bits);
    logic [15:0] checksum;
    integer idx;
    begin
      checksum = 16'h0000;
      for (idx = 0; idx < 7; idx++) begin
        checksum ^= frame_bits[16 + idx*16 +: 16];
      end
      return checksum;
    end
  endfunction

  assign action = action_t'(in_action_data);
  assign in_ready = !out_valid || out_ready;

  always_comb begin
    encoded_frame = '0;
    encoded_frame[127:120] = action.action_type;
    encoded_frame[119:88] = action.price;
    encoded_frame[87:56] = action.qty;
    encoded_frame[55:48] = output_reason_code(action.action_type, action.reason_code);
    encoded_frame[47:16] = (action.timestamp != 32'd0) ? action.timestamp : now_ts;
    encoded_frame[15:0] = checksum16(encoded_frame);
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      out_valid <= 1'b0;
      out_data <= '0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        out_data <= encoded_frame;
      end
    end
  end
endmodule
