restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_0")}
run 5.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 95.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_1")}
run 15.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 85.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_2")}
run 25.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 75.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_3")}
run 35.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 65.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_4")}
run 45.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 55.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_5")}
run 55.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 45.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_6")}
run 65.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 35.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_7")}
run 75.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 25.0
restart
call {$runfault("s27_tb.s27_inst.DFF_0.NOTIFIER_8")}
run 85.0
force {s27_tb.s27_inst.DFF_0.NOTIFIER} x -deposit
run 15.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_0")}
run 5.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 95.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_1")}
run 15.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 85.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_2")}
run 25.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 75.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_3")}
run 35.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 65.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_4")}
run 45.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 55.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_5")}
run 55.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 45.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_6")}
run 65.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 35.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_7")}
run 75.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 25.0
restart
call {$runfault("s27_tb.s27_inst.DFF_1.NOTIFIER_8")}
run 85.0
force {s27_tb.s27_inst.DFF_1.NOTIFIER} x -deposit
run 15.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_0")}
run 5.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 95.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_1")}
run 15.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 85.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_2")}
run 25.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 75.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_3")}
run 35.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 65.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_4")}
run 45.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 55.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_5")}
run 55.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 45.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_6")}
run 65.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 35.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_7")}
run 75.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 25.0
restart
call {$runfault("s27_tb.s27_inst.DFF_2.NOTIFIER_8")}
run 85.0
force {s27_tb.s27_inst.DFF_2.NOTIFIER} x -deposit
run 15.0

quit -f
