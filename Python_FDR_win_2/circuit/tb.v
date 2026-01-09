module tb;
    reg tb_clk;
    reg tb_d;
    wire tb_q;

    test inst(.clk(tb_clk),
                .d(tb_d),
                .q(tb_q));

    initial begin
        tb_clk <= 1'b0;
        forever #10 tb_clk <= ~tb_clk;
    end

    initial begin
        tb_d = 1'b0;
        #20 tb_d = 1'b1;
        #20 tb_d = 1'b0;
        #20 tb_d = 1'b1;
        #20 tb_d = 1'b0;
        #20 tb_d = 1'b1;
        #20 tb_d = 1'b0;
        #20 tb_d = 1'b1;
        #20 tb_d = 1'b0;
        #20 tb_d = 1'b1;
        #100;
    end

endmodule