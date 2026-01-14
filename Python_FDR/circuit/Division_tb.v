`timescale 1ns / 1ns

module Division_tb_v;

	// Inputs
	reg [31:0] dividend;
	reg [31:0] divider;
	reg sign;
	reg clk;

	// Outputs
	wire ready;
	wire [31:0] quotient;
	wire [31:0] remainder;
	
	// Variables
	integer i ; 

	// Instantiate the Unit Under Test (UUT)
	Division uut (
		.ready(ready), 
		.quotient(quotient), 
		.remainder(remainder), 
		.dividend(dividend), 
		.divider(divider), 
		.sign(sign), 
		.clk(clk)
	);

	initial begin
	//Check for unsigned division
	clk = 0;
	#10;

	// dividend = 32'd4;
	// divider = 32'd2;
	// sign = 0;
	// for(i=0;i<66;i=i+1)
	// begin
	// clk = ~clk;
	// #10;
	// end
	
	//To check for signed division
	// dividend = 32'd8;
	// divider = 32'd2;
	// sign = 1;
	// for(i=0;i<66;i=i+1)
	// begin
	// clk = ~clk;
	// #10;
	// end
	
	//To check for remainder 
	dividend = 32'd100;
	divider = 32'd9;
	sign = 1;
	for(i=0;i<1000;i=i+1)
	begin
	clk = ~clk;
	#10;
	end
	
	end
	
	
      
endmodule
