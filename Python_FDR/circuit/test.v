module test(
    input       clk, 
    input       d,
    output reg  q
);
    
    reg w0, w1, w2, w3;
    wire w4;

    assign w4 = (w1 & w2) | (w1 & w3) |(w2 & w3);

    always @(posedge clk) begin
        w0 <= d;
    end

    always @(posedge clk) begin
        w1 <= w0;
    end
    always @(posedge clk) begin
        w2 <= w0;
    end
    always @(posedge clk) begin
        w3 <= w0;
    end

    always @(posedge clk) begin
        q <= w4;
    end

endmodule