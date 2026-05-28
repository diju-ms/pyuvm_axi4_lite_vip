# ─────────────────────────────────────────────────────────────────────────────
#
# Usage:
#   make                     run all tests with verilator
#   make SIM=questa          run with Questa
#   make TEST=TestReset      run a single named test
#   make WAVES=1             open GTKWave after run (Icarus only)
# ─────────────────────────────────────────────────────────────────────────────


PWD=$(shell pwd)
SIM ?= verilator
TOPLEVEL_LANG ?= verilog

#top design unit name
COCOTB_TOPLEVEL     := axi_lite_slave_v1_0_S00_AXI

#top python tb file name
COCOTB_TEST_MODULES := main

# design/ is one level up from tb/
DESIGN_DIR = $(PWD)/../rtl

# top leel project path
export PYTHONPATH := $(PWD)/..:$(PYTHONPATH)


# 1. MOVE LINT FLAGS HERE (At the top, before rules)
# EXTRA_ARGS += -Wno-WIDTHTRUNC
ifeq ($(SIM),verilator)
  COMPILE_ARGS += --timing        # required for cocotb with Verilator
  COMPILE_ARGS += --assert        # enable SVA (partial support)
  COMPILE_ARGS += -Wall           # recommended
  COMPILE_ARGS += -Wno-EOFNEWLINE #to avoid lint issue %Warning-EOFNEWLINE: Missing newline at end of file
  COMPILE_ARGS += -Wno-WIDTHTRUNC #to avoid lint issue for size mismatches
  COMPILE_ARGS += -I$(DESIGN_DIR) # compiler flag that stands for Include. It tells the compiler, "Hey, when you are looking for header files (like .h in C/C++) or package/include files (like .vh or .svh in Verilog), look inside the directory I'm about to specify."
endif 


# Simulator-specific flags
ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif
ifeq ($(SIM),questa)
  COMPILE_ARGS += -sv
  SIM_ARGS     += -do "log -r /*; run -all"
endif
ifeq ($(SIM),vcs)
  COMPILE_ARGS += -sverilog +v2k
endif



ifeq ($(TOPLEVEL_LANG),verilog)
    VERILOG_SOURCES = $(DESIGN_DIR)/axi_lite_slave_v1_0_S00_AXI.v
else
    $(error A valid value (verilog or vhdl) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG))
endif


# Cocotb include line
include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: waves clean_all
waves:
	gtkwave dump.vcd &

clean_all: clean
	rm -rf __pycache__ results.xml dump.vcd sim_build

