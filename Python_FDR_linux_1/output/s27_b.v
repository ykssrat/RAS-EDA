// Partition b from s27
// Contains 7 instances

module s27_b (CK, G1, cut_G11, cut_G16, G17, G2, cut_G5, cut_G8);
  input CK, G1, cut_G16, G2, cut_G5, cut_G8;
  output cut_G11, G17;

  wire G11, G12, G13, G15, G16, G5, G7, G8, G9;

  assign cut_G11 = G11;
  assign G16 = cut_G16;
  assign G5 = cut_G5;
  assign G8 = cut_G8;

// Instances assigned to partition b
  NOR2_X1 NOR2_2 (.ZN(G12), .A1(G1), .A2(G7));
  DFF_X1 DFF_2 (.CK(CK), .Q(G7), .D(G13));
  OR2_X1 OR2_0 (.ZN(G15), .A1(G12), .A2(G8));
  NOR2_X1 NOR2_1 (.ZN(G11), .A1(G5), .A2(G9));
  NOR2_X1 NOR2_3 (.ZN(G13), .A1(G2), .A2(G12));
  NAND2_X1 NAND2_0 (.ZN(G9), .A1(G16), .A2(G15));
  INV_X1 NOT_1 (.ZN(G17), .A(G11));

endmodule  // s27_b