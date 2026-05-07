package pim_prims;
  function automatic logic cmp_price_ge(
    input logic signed [31:0] lhs,
    input logic signed [31:0] rhs
  );
    return lhs >= rhs;
  endfunction

  function automatic logic signed [31:0] min_price(
    input logic signed [31:0] lhs,
    input logic signed [31:0] rhs
  );
    return (lhs <= rhs) ? lhs : rhs;
  endfunction

  function automatic logic signed [31:0] max_price(
    input logic signed [31:0] lhs,
    input logic signed [31:0] rhs
  );
    return (lhs >= rhs) ? lhs : rhs;
  endfunction
endpackage
