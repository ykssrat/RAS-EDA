module s27_tb;
  reg CK, G0, G1, G2, G3;
  wire G17;

  s27 s27_inst(.*);

  initial begin
    CK = 0;
    forever begin
      #5 CK = ~CK;
    end
  end

  initial begin
    {G0, G1, G2, G3} = 4'b1111;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b1011;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b0110;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b1000;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b0101;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b1011;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b0000;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b1100;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b0010;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b1101;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b0011;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b1100;
    @(negedge CK);
    {G0, G1, G2, G3} = 4'b0111;
    @(negedge CK);
    #3 $finish;
  end

  // initial begin
  //   $monitor("{G0, G1, G2, G3} = %b, G17 = %b",{G0, G1, G2, G3}, G17);
  // end

endmodule