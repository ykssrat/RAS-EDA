`timescale 1ns/1ps

module s27_bench_tb;
    // Inputs
    reg blif_clk_net;
    reg blif_reset_net;
    reg G0;
    reg G1;
    reg G2;
    reg G3;

    // Outputs
    wire G17;

    // Instantiate the Unit Under Test (UUT)
    s27_bench uut (
        .blif_clk_net(blif_clk_net),
        .blif_reset_net(blif_reset_net),
        .G0(G0),
        .G1(G1),
        .G2(G2),
        .G3(G3),
        .G17(G17)
    );

    initial begin
        blif_clk_net = 0;
        forever #5 blif_clk_net = ~blif_clk_net;
    end

    initial begin
        // Initialize Inputs
        blif_clk_net = 0;
        blif_reset_net = 0;
        G0 = 0;
        G1 = 0;
        G2 = 0;
        G3 = 0;

        // Reset
        blif_reset_net = 1;
        #20 blif_reset_net = 0;

        // Basic Random Stimulus
        repeat (100) begin
            #10;
            G0 = $random;
            G1 = $random;
            G2 = $random;
            G3 = $random;
        end
        
        #100 $finish;
    end

endmodule
