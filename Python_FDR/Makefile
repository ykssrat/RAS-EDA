.PHONY:com sim clean wave all vcd dve

SHELL := /bin/bash

OUTPUT 	= sim
CSOURCE = ./clibrary/main.c
TAB 	= ./clibrary/pli.tab
VFILE 	= ./circuit/verilog_file.f
UCLI    = run.tcl

VCS_CMD ?= vcs

VCS = ${VCS_CMD} ${VCS_EXTRA_FLAGS} -sverilog +v2k 	 					\
      -timescale=1ns/1ns   						\
	  -debug_all								\
	  -o ${OUTPUT}								\
	  -l compile.log							\
	  -full64									\
      +memcbk									\
	  #-use_vpiobj vpi_user.c +vpi

SIM = ./${OUTPUT} \
	  ${SIM_EXTRA_FLAGS} \
	  -ucli -i ${UCLI} \
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
# 保留 output/ 下的用户分析产物；若需要一并清理使用 distclean
.PHONY: distclean
distclean:
	rm -rf ./output/*


