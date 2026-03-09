`timescale 1ns/1ps

module s1423_bench_tb;
    // Inputs
    reg blif_clk_net;
    reg blif_reset_net;
    reg G0;
    reg G1;
    reg G2;
    reg G3;
    reg G4;
    reg G5;
    reg G6;
    reg G7;
    reg G8;
    reg G9;
    reg G10;
    reg G11;
    reg G12;
    reg G13;
    reg G14;
    reg G15;
    reg G16;

    // Outputs
    wire G726;
    wire G729;
    wire G702;
    wire G727;
    wire G701BF;

    // Instantiate the Unit Under Test (UUT)
    s1423_bench uut (
        .blif_clk_net(blif_clk_net),
        .blif_reset_net(blif_reset_net),
        .G0(G0),
        .G1(G1),
        .G2(G2),
        .G3(G3),
        .G4(G4),
        .G5(G5),
        .G6(G6),
        .G7(G7),
        .G8(G8),
        .G9(G9),
        .G10(G10),
        .G11(G11),
        .G12(G12),
        .G13(G13),
        .G14(G14),
        .G15(G15),
        .G16(G16),
        .G726(G726),
        .G729(G729),
        .G702(G702),
        .G727(G727),
        .G701BF(G701BF)
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
        G4 = 0;
        G5 = 0;
        G6 = 0;
        G7 = 0;
        G8 = 0;
        G9 = 0;
        G10 = 0;
        G11 = 0;
        G12 = 0;
        G13 = 0;
        G14 = 0;
        G15 = 0;
        G16 = 0;

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
            G4 = $random;
            G5 = $random;
            G6 = $random;
            G7 = $random;
            G8 = $random;
            G9 = $random;
            G10 = $random;
            G11 = $random;
            G12 = $random;
            G13 = $random;
            G14 = $random;
            G15 = $random;
            G16 = $random;
        end
        
        #100 $finish;
    end

endmodule
