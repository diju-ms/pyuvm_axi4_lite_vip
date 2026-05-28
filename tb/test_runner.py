import os
import sys
import glob
import logging
from pathlib import Path
# 1. FIXED: Using the modern cocotb_tools library import path
from cocotb_tools.runner import get_runner

# ==============================================================================
# CONFIGURATION SETTINGS (Declared at the top for easy changes)
# ==============================================================================
SIM_CHOICE = os.getenv("SIM", "verilator")
TOP_MODULE = os.getenv("TOPLEVEL", "axi_lite_slave_v1_0_S00_AXI")
TEST_FILE  = os.getenv("MODULE", "main")

# Setup project workspace directories
tb_path = Path(__file__).resolve().parent
repo_root = tb_path.parent
rtl_dir = repo_root / "rtl"

# ==============================================================================
# LOGGING SETUP (Dual Stream Capture)
# ==============================================================================
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Stream 1: Keep live console output active
c_handler = logging.StreamHandler(sys.stdout)
c_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(c_handler)

# Stream 2: Simultaneously duplicate output into srun.log
f_handler = logging.FileHandler("srun.log", mode="w")
f_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(f_handler)

# Environment configuration for VIP package imports
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))
os.environ["PYTHONPATH"] = str(repo_root) + os.pathsep + os.environ.get("PYTHONPATH", "")

def test_axi_lite_slave():
    # Discover Verilog (.v) and SystemVerilog (.sv) files dynamically
    sources = list(rtl_dir.glob("*.v")) + list(rtl_dir.glob("*.sv"))
    sources = [str(s.resolve()) for s in sources]

    # Initialize tool argument lists
    build_args = []
    test_args = []
    wave_flag = False

    # Multi-simulator flag block
    if SIM_CHOICE == "verilator":
        build_args.extend([
            "--timing",
            "--assert",
            "-Wall",
            "-Wno-EOFNEWLINE",
            "-Wno-WIDTHTRUNC",
            f"-I{rtl_dir.resolve()}"
        ])
        
        # Wave tracking triggers
        if os.environ.get("WAVES") == "1":
            # Tell compiler to prepare tracing blocks
            build_args.extend(["--trace-fst", "--trace-structs"])
            # Tell runtime engine to execute tracing
            wave_flag = True
            # FIXED: Force Verilator executable to output dump.fst directly into the tb/ folder
            test_args.append(f"--dump-file={tb_path / 'dump.fst'}")

    # Initialize the target runner instance
    runner = get_runner(SIM_CHOICE)
    
    # Compile the hardware assets
    runner.build(
        sources=sources,
        hdl_toplevel=TOP_MODULE,
        build_args=build_args,
        clean=True,
    )
    
    # Execute the test routines
    runner.test(
        hdl_toplevel=TOP_MODULE, 
        test_module=TEST_FILE,
        test_args=test_args,
        waves=wave_flag  # Built-in Cocotb trace trigger switch
    )

    # Post-Processing: Collect sub-directory run telemetry
    try:
        subdirectory = "sim_build"
        file_pattern = os.path.join(subdirectory, "srun_*")
        srun_files = glob.glob(file_pattern)
        output_file = "xrun.log"

        if srun_files:
            with open(output_file, "w") as outfile:
                for file_path in srun_files:
                    if os.path.isfile(file_path):
                        with open(file_path, "r") as infile:
                            outfile.write(infile.read())
                            outfile.write("\n")
            logger.info(f"Aggregated xrun log created at: {output_file}")
    except Exception as e:
        logger.error(f"Failed log aggregation pass: {str(e)}")

if __name__ == "__main__":
    test_axi_lite_slave()
