`timescale 1ns/1ps

module s382_bench_tb;
    // Inputs
    reg blif_clk_net;
    reg blif_reset_net;
    reg FM;
    reg TEST;
    reg CLR;

    // Outputs
    wire GRN1;
    wire GRN2;
    wire RED1;
    wire YLW2;
    wire RED2;
    wire YLW1;

    // Instantiate the Unit Under Test (UUT)
    s382_bench uut (
        .blif_clk_net(blif_clk_net),
        .blif_reset_net(blif_reset_net),
        .FM(FM),
        .TEST(TEST),
        .CLR(CLR),
        .GRN1(GRN1),
        .GRN2(GRN2),
        .RED1(RED1),
        .YLW2(YLW2),
        .RED2(RED2),
        .YLW1(YLW1)
    );

    initial begin
        blif_clk_net = 0;
        forever #5 blif_clk_net = ~blif_clk_net;
    end

    initial begin
        // Initialize Inputs
        blif_clk_net = 0;
        blif_reset_net = 0;
        FM = 0;
        TEST = 0;
        CLR = 0;

        // Reset
        blif_reset_net = 1;
        #20 blif_reset_net = 0;

        // Basic Random Stimulus
        repeat (100) begin
            #10;
            FM = $random;
            TEST = $random;
            CLR = $random;
        end
        
        #100 $finish;
    end

endmodule
