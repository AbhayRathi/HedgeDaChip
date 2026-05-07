interface vr_if #(
  parameter int W = 128,
  parameter int U = 1,
  parameter bit HAS_LAST = 0,
  parameter bit HAS_USER = 0
);
  logic valid;
  logic ready;
  logic [W-1:0] data;
  logic last;
  logic [U-1:0] user;

  modport producer (
    output valid,
    output data,
    output last,
    output user,
    input ready
  );

  modport consumer (
    input valid,
    input data,
    input last,
    input user,
    output ready
  );
endinterface
