
module AND2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  and(ZN, A1, A2);

  specify
    (A1 => ZN) = (0.1, 0.1);
    (A2 => ZN) = (0.1, 0.1);
  endspecify

endmodule

primitive \seq_DFF_X1  (IQ, nextstate, CK, NOTIFIER);
  output IQ;
  input nextstate;
  input CK;
  input NOTIFIER;
  reg IQ;

  table
// nextstate          CK    NOTIFIER     : @IQ :          IQ
           0           r           ?       : ? :           0;
           1           r           ?       : ? :           1;
           0           *           ?       : 0 :           0; // reduce pessimism
           1           *           ?       : 1 :           1; // reduce pessimism
           *           ?           ?       : ? :           -; // Ignore all edges on nextstate
           ?           n           ?       : ? :           -; // Ignore non-triggering clock edge
           ?           ?           *       : ? :           x; // Any NOTIFIER change
  endtable
endprimitive

module DFF_X1 (D, CK, Q, QN);
  input D;
  input CK;
  output Q;
  output QN;
  reg NOTIFIER;

  `ifdef NTC
    \seq_DFF_X1 (IQ, nextstate, CK_d, NOTIFIER);
    not(IQN, IQ);
    buf(Q, IQ);
    buf(QN, IQN);
    buf(nextstate, D_d);

  `else
    \seq_DFF_X1 (IQ, nextstate, CK, NOTIFIER);
    not(IQN, IQ);
    buf(Q, IQ);
    buf(QN, IQN);
    buf(nextstate, D);

  `endif

  specify
    (posedge CK => (Q +: D)) = (0.1, 0.1);
    (posedge CK => (QN -: D)) = (0.1, 0.1);
    `ifdef NTC
      $setuphold(posedge CK, negedge D, 0.1, 0.1, NOTIFIER, , ,CK_d, D_d);
      $setuphold(posedge CK, posedge D, 0.1, 0.1, NOTIFIER, , ,CK_d, D_d);
      $width(negedge CK, 0.1, 0, NOTIFIER);
      $width(posedge CK, 0.1, 0, NOTIFIER);
    `else
      $setuphold(posedge CK, negedge D, 0.1, 0.1, NOTIFIER);
      $setuphold(posedge CK, posedge D, 0.1, 0.1, NOTIFIER);
      $width(negedge CK, 0.1, 0, NOTIFIER);
      $width(posedge CK, 0.1, 0, NOTIFIER);
    `endif
  endspecify

endmodule

module INV_X1 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);

  specify
    (A => ZN) = (0.1, 0.1);
  endspecify

endmodule


module NAND2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_10);
  and(i_10, A1, A2);

  specify
    (A1 => ZN) = (0.1, 0.1);
    (A2 => ZN) = (0.1, 0.1);
  endspecify

endmodule

module NOR2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_10);
  or(i_10, A1, A2);

  specify
    (A1 => ZN) = (0.1, 0.1);
    (A2 => ZN) = (0.1, 0.1);
  endspecify

endmodule

module OR2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  or(ZN, A1, A2);

  specify
    (A1 => ZN) = (0.1, 0.1);
    (A2 => ZN) = (0.1, 0.1);
  endspecify

endmodule


