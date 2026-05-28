import os 
import sys
import glob
from pathlib import Path  
  
from cocotb_tools.runner import get_runner  
import logging
# Configure logging
# Configure the logger
logging.basicConfig(
    filename='xrun.log',          # Output to xrun.log
    level=logging.DEBUG,          # Log level
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)
# Create a logger
logger = logging.getLogger()


toplevel = "axi_lite_slave_v1_0_S00_AXI"
module = "main"

repo_root = Path(__file__).resolve().parent.parent
tb_path = Path(__file__).resolve().parent

# Get desing path
rtl_dir = repo_root / "rtl"

sources = [rtl_dir / "axi_lite_slave_v1_0_S00_AXI.v"]  
print(f"DEBUG: Checking RTL Path -> {(rtl_dir / 'axi_lite_slave_v1_0_S00_AXI.v').resolve()}")


# 1. Initialize empty lists for arguments
build_args = []
test_args = []
plus_args = []  # Added for plusarg control parameters


# 1. Update the local script path
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

# 2. FIX: Force the OS environment to pass the path down to the simulator
# This ensures Verilator/Cocotb can see the 'vip' folder during execution
os.environ["PYTHONPATH"] = str(repo_root) + os.pathsep + os.environ.get("PYTHONPATH", "")


  
def test_my_design_runner():  
    sim = os.getenv("SIM", "verilator")  
    waves=1 


    # 2. Add flags ONLY if we are using Verilator
    if sim == "verilator":
        build_args.extend([
            "--timing",
            "--assert",
            "-Wall",
            "-Wno-EOFNEWLINE",
            "-Wno-WIDTHTRUNC",
            f"-I{rtl_dir}"
        ])
        
        # Guarded wave tracing for Verilator
        if os.environ.get("WAVES") == "1":
            build_args.extend(["--trace-fst", "--trace-structs"])
            test_args.append("--trace")

    # 3. Add flags for other simulators if you use them later
    elif sim == "icarus":
        if os.environ.get("WAVES") == "1":
            # Icarus handles waveforms via runtime target VVP flags
            test_args.append("-fst")  

    # Safe Wave Tracing configuration block
    if os.environ.get("WAVES") == "1":
        # 1. Instruct compiler to bake the trace infrastructure
        build_args.extend(["--trace-fst", "--trace-structs"])
        # 2. Tell the test interface to initialize the trace runtime engine
        test_args.append("--trace")
        # 3. FIX: Force the file path to dump directly in your current folder
        plus_args.append("+dumpfile_path=dump.fst")


###    dut_file = rtl_dir / "axi_lite_slave_v1_0_S00_AXI.v"

    # Create sim_build directory if it doesn't exist
    sim_build_dir = repo_root / "tb/sim_build"
    sim_build_dir.mkdir(exist_ok=True)

    # Source files
 #   sources = [
 #       proj_path / "hdl" / "verilog" / "tinyalu.sv"
 #   ]
  
    runner = get_runner(sim) 

#    # Set environment variables to control waveform dumping
#    os.environ["COCOTB_DUMP_WAVE_FORMAT"] = "vcd"  # Use vcd format
#    # Set VCD_NAME to specify the output VCD file name  
#    #env = os.environ.copy()  
#    os.environ["VCD_NAME"] = "my_wave.vcd"  


    runner.build(
        sources=sources,
        hdl_toplevel=toplevel,
        build_args=build_args,
        clean=True,
#        waves=True,  
#        build_args =["--trace","-Wno-WIDTHTRUNC"],  # Enable VCD tracing in Verilator  
    )
    
    runner.test(
        hdl_toplevel=toplevel, 
        test_module=module,
        test_args=test_args,
        log_file = "srun.log",
        plusargs=plus_args,
#        seed = None,
#        testcase = "Allsame_Test",
#        #plusargs=["+UVM_TESTNAME=AluTest"], # Pass the specific pyuvm test name
    ) 
  
  
if __name__ == "__main__":  
    test_my_design_runner()
    logger.info("All run information will be in copied from sim_build/srun.log")

    # 1. Define the pattern for the input files
    subdirectory = "sim_build"
    file_pattern = os.path.join(subdirectory, "srun_*")
    output_file = "xrun.log"
    
    print(f"Starting log aggregation. All files matching '{file_pattern}' will be copied to '{output_file}'.")
    print("-" * 40)
    
    # Use glob to find all files matching the pattern in the current directory
    srun_files = glob.glob(file_pattern)
    
    if not srun_files:
        print(f"No files found matching the pattern: {file_pattern}")
    else:
        # 2. Open the output file in append mode ('a')
        # Use 'w' instead of 'a' if you want to overwrite 'xrun.log' each time.
        try:
            with open(output_file, 'a') as outfile:
                
                # Iterate over the found files
                for file_path in srun_files:
                    
                    # Skip directories if glob happens to find a directory matching the pattern
                    if os.path.isdir(file_path):
                        continue
    
                    try:
                        # Before copying, print the file path to the output log
                        # The line is formatted to be a clear separator in the log file
                        header_line = f"\n\n--- Content from file: {file_path} ---\n"
                        outfile.write(header_line)
                        print(f"Processing: {file_path}")

                        # 3. Read the content of the current file and copy it
                        with open(file_path, 'r') as infile:
                            # Read the entire content
                            content = infile.read()
                            # Write the content to the output file
                            outfile.write(content)
                            
                    except IOError as e:
                        # Handle errors during reading/writing of individual files
                        print(f"Error processing file {file_path}: {e}")
                        outfile.write(f"\n[ERROR] Could not read file: {e}\n")
                        
                outfile.write(f"\n--- Log aggregation complete ---\n")
    
            print("-" * 40)
            print(f"Log aggregation complete. Content has been appended to '{output_file}'.\n")
    
        except IOError as e:
            # Handle errors for the main output file
            print(f"Critical error: Could not open or write to output file '{output_file}': {e}")
    
