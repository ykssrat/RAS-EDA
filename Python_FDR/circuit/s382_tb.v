module s382_tb;
  reg CK, FM, TEST, CLR;
  wire GRN1,GRN2,RED1,YLW2,RED2,YLW1;

  s382 s382_inst(.*);

  initial begin
    CK = 0;
    forever begin
      #5 CK = ~CK;
    end
  end

  initial begin
    {FM, TEST, CLR} = 3'b111;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b000;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b111;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b011;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b110;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b001;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b101;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b000;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b100;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b010;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b111;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b000;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b101;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b011;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b101;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b110;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b010;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b100;
    @(negedge CK);
    {FM, TEST, CLR} = 3'b101;
    @(negedge CK);
    #3 $finish;
  end

  initial begin
    $monitor("{FM, TEST, CLR} = %b, {GRN1, GRN2, RED1, YLW2, RED2, YLW1} = %b",{FM, TEST, CLR}, {GRN1,GRN2,RED1,YLW2,RED2,YLW1});
  end

endmodule