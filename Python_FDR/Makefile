.PHONY:com sim clean wave all vcd dve

OUTPUT 	= sim
CSOURCE = ./clibrary/main.c
TAB 	= ./clibrary/pli.tab
VFILE 	= ./circuit/verilog_file.f
UCLI    = run.tcl

VCS = vcs -sverilog +v2k 	 					\
      -timescale=1ns/1ns   						\
	  -debug_all								\
	  -o ${OUTPUT}								\
	  -l compile.log							\
	  -full64									\
      +memcbk									\
	  #-use_vpiobj vpi_user.c +vpi

SIM = ./${OUTPUT} 			\
	  -ucli -i ${UCLI}	 	\
	  -ucli2Proc            \
	  #-l run.log

com:
	${VCS} -f ${VFILE} -P ${TAB} ${CSOURCE}

sim:
	${SIM}

wave:
	${SIM} -gui

all:
	make com
	make sim

vcd:
	dve -full64 -vpd trace.vcd

dve:
	dve -vpd vcdplus.vpd &

clean:
	rm -rf ./csrc *.daidir *.log simv* *.key \
	*.vpd ${OUTPUT} DVEfiles *.vcd *.fsdb save.ucli \
	save.FILES ./output/* ./ucli_file ./clibrary/test \
	./*.o



