// Partition a from s27
// Contains 6 instances

module s27_a (CK, G0, cut_G11, cut_G16, G3, cut_G5, cut_G8);
  input CK, G0, cut_G11, G3;
  output cut_G16, cut_G5, cut_G8;

  wire G10, G11, G14, G16, G5, G6, G8;

  assign G11 = cut_G11;
  assign cut_G16 = G16;
  assign cut_G5 = G5;
  assign cut_G8 = G8;

// Instances assigned to partition a
  DFF_X1 DFF_1 (.CK(CK), .Q(G6), .D(G11));
  AND2_X1 AND2_0 (.ZN(G8), .A1(G14), .A2(G6));
  NOR2_X1 NOR2_0 (.ZN(G10), .A1(G14), .A2(G11));
  INV_X1 NOT_0 (.ZN(G14), .A(G0));
  DFF_X1 DFF_0 (.CK(CK), .Q(G5), .D(G10));
  OR2_X1 OR2_1 (.ZN(G16), .A1(G3), .A2(G8));

endmodule  // s27_a