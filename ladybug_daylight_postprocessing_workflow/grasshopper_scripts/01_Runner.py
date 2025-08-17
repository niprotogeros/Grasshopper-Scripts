# GhPython (IronPython 2.7) - Component 1: ANALYSIS RUNNER

import os, sys, subprocess

# ==============================================================================
# --- GRASSHOPPER COMPONENT DOCUMENTATION ---
# ==============================================================================
# Set the component description
ghenv.Component.Description = (
    "This is the main 'engine' of the post-processing workflow.\n\n"
    "It takes all the required thresholds and file paths, then executes an "
    "external CPython script to perform the heavy calculations for BREEAM, "
    "UDI, sDA, and ASE. Its primary output is the file path to the generated "
    "'daylight_summary.json' file, which the 'Reader' components use."
)

# Set input descriptions
try:
    ghenv.Component.Params.Input[0].Description = "Set to True to execute the external analysis script."
    ghenv.Component.Params.Input[1].Description = "Path to the Ladybug Tools simulation folder containing the 'results' subfolder."
    ghenv.Component.Params.Input[2].Description = "The BREEAM minimum illuminance threshold (e.g., 300 lux)."
    ghenv.Component.Params.Input[3].Description = "The BREEAM required hours for the minimum threshold (e.g., 2000 hours)."
    ghenv.Component.Params.Input[4].Description = "The BREEAM spatial average illuminance threshold (e.g., 100 lux)."
    ghenv.Component.Params.Input[5].Description = "The BREEAM required hours for the average threshold (e.g., 4000 hours)."
    ghenv.Component.Params.Input[6].Description = "The 'useful' minimum illuminance for UDI calculations (e.g., 100 or 300 lux)."
except: pass # Fails gracefully if inputs are not yet defined

# Set output descriptions
try:
    ghenv.Component.Params.Output[0].Description = "A summary message indicating the script's status (running, success, or error)."
    ghenv.Component.Params.Output[1].Description = "The full output (stdout and stderr) from the external Python script. Useful for debugging."
    ghenv.Component.Params.Output[2].Description = "The file path to the generated 'daylight_summary.json' file. Connect this to the reader components."
except: pass # Fails gracefully if outputs are not yet defined

# ==============================================================================
# --- SCRIPT CONFIGURATION AND LOGIC ---
# ==============================================================================

# --- CONFIGURATION (EDIT THESE PATHS) ---
PYTHON_EXECUTABLE_PATH = r"C:\Python_Scripts\lbt-venv\Scripts\python.exe"
EXTERNAL_SCRIPT_PATH = r"C:\Python_Scripts\post_process_daylight_all_grids.py"

# --- INITIALIZE OUTPUTS ---
message = "Set 'run_analysis' to True."
log = "Waiting for analysis to run..."
json_file_path = None

# --- MAIN LOGIC ---
if run_analysis:
    errors = []
    if not os.path.exists(PYTHON_EXECUTABLE_PATH): errors.append("Python executable not found.")
    if not os.path.exists(EXTERNAL_SCRIPT_PATH): errors.append("External script not found.")
    if not results_folder or not os.path.isdir(results_folder): errors.append("Invalid 'results_folder'.")
    
    if errors:
        message = "[ERROR]\n" + "\n".join(errors)
    else:
        try:
            message = "[INFO] Running external analysis script... Please wait."
            command_args = [
                PYTHON_EXECUTABLE_PATH, EXTERNAL_SCRIPT_PATH,
                results_folder, str(min_lux), str(min_hours_req),
                str(avg_lux), str(avg_hours_req), str(udi_min_lux)
            ]
            proc = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout, stderr = proc.communicate()
            log = stdout + stderr

            if proc.returncode != 0:
                message = "[ERROR] External script failed. Check 'log' for details."
            else:
                summary_file = os.path.join(results_folder, "daylight_summary.json")
                if not os.path.exists(summary_file):
                    message = "[ERROR] Script ran but 'daylight_summary.json' was not created."
                else:
                    message = "[SUCCESS] Analysis complete. Results file is ready."
                    json_file_path = summary_file

        except Exception as e:
            message = "[FATAL ERROR] An exception occurred:\n" + str(e)