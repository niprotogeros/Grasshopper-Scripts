# Daylight Post-Processing Workflow Installation Guide

This guide provides step-by-step instructions for setting up the automated daylight analysis post-processing workflow on a new computer.

The workflow uses Rhino/Grasshopper and an external Python script to calculate BREEAM, UDI, sDA, and ASE metrics from Ladybug Tools simulation results.

## Prerequisites

Before you begin, ensure the following software is installed:

1.  **Rhino 7**
2.  **Ladybug Tools for Grasshopper (v1.8 or newer)**: Follow the official installation instructions from [Food4Rhino](https://www.food4rhino.com/en/app/ladybug-tools) or the [Ladybug Tools Discourse Forum](https://discourse.ladybug.tools/t/lbt-1-8-0-stable-release/21929). This is a critical prerequisite.

## Installation Steps

### Step 1: Set Up the Python Environment

This workflow uses an external CPython script that requires the `numpy` library. We will create a dedicated virtual environment to manage this dependency.

1.  **Install Python:**
    *   Download and install Python 3.8 or a later version from the official website: [python.org](https://www.python.org/downloads/).
    *   **IMPORTANT**: During installation, make sure to check the box that says **"Add Python to PATH"**.

2.  **Create a Project Folder:**
    *   Create a dedicated folder on your computer to store the Python scripts. For this guide, we will use `C:\Python_Scripts`.

3.  **Create a Virtual Environment:**
    *   Open the Windows Command Prompt (`cmd`).
    *   Navigate to your new folder by typing:
        ```bash
        cd C:\Python_Scripts
        ```
    *   Create a virtual environment named `lbt-venv`:
        ```bash
        python -m venv lbt-venv
        ```

4.  **Activate the Environment and Install Libraries:**
    *   Activate the new environment:
        ```bash
        lbt-venv\Scripts\activate
        ```
        (Your command prompt line should now start with `(lbt-venv)`).
    *   Place the `requirements.txt` file inside the `C:\Python_Scripts` folder.
    *   Install the necessary library (`numpy`) using the requirements file:
        ```bash
        pip install -r requirements.txt
        ```
    *   You can now close the command prompt.

### Step 2: Place the External Script

1.  Take the external Python script (`post_process_daylight_all_grids.py`) and place it inside your project folder: `C:\Python_Scripts`.

Your `C:\Python_Scripts` folder should now contain:
*   `post_process_daylight_all_grids.py`
*   `requirements.txt`
*   A folder named `lbt-venv`

### Step 3: Configure the Grasshopper Components

Open Rhino and Grasshopper. Create three new `GHPython Script` components on the canvas. We will configure each one as follows.

---

#### A. Component 1: Daylight Analysis RUNNER

1.  **Rename the component** to `Daylight Analysis RUNNER`.
2.  **Right-click** and open the editor. Copy and paste the full script for the **Runner** component.
3.  **CRITICAL:** In the script editor, you **must edit** the two configuration paths at the top to match your system:
    ```python
    PYTHON_EXECUTABLE_PATH = r"C:\Python_Scripts\lbt-venv\Scripts\python.exe"
    EXTERNAL_SCRIPT_PATH = r"C:\Python_Scripts\post_process_daylight_all_grids.py"
    ```
4.  **Set up the inputs:** Zoom in on the component and use the `+` icons, then right-click each input to rename it and set its **Type hint**.
    *   `run_analysis` (Type hint: `bool`)
    *   `results_folder` (Type hint: `str`)
    *   `min_lux` (Type hint: `float`)
    *   `min_hours_req` (Type hint: `int`)
    *   `avg_lux` (Type hint: `float`)
    *   `avg_hours_req` (Type hint: `int`)
    *   `udi_min_lux` (Type hint: `float`)

5.  **Understand the outputs:** The component will automatically create the following outputs:
    *   `message`: A summary message indicating the script's status (running, success, or error).
    *   `log`: The full output (stdout and stderr) from the external Python script. This is very useful for debugging.
    *   `json_file_path`: The file path to the generated `daylight_summary.json` file. **Connect this to the reader components.**

---

#### B. Component 2: BREEAM Results READER

1.  **Rename the component** to `BREEAM Reader`.
2.  **Right-click** and open the editor. Copy and paste the full script for the **BREEAM Reader** component.
3.  **Set up the inputs:**
    *   `json_file_path` (Type hint: `str`)
    *   `grid_meshes` (Type hint: `Mesh`, **Access: `List`**)
    *   `grid_names` (Type hint: `str`, **Access: `List`**)

4.  **Understand the outputs:** This component provides all BREEAM-related results:
    *   `message`: A status message for the BREEAM reader.
    *   `building_pass`: A single `True`/`False` value indicating if the entire building passes.
    *   `worst_room`: The name of the room with the worst BREEAM performance.
    *   `room_labels`: The cleaned room names used for matching results.
    *   `room_min_pass`: A list of `True`/`False` values for the **minimum** illuminance criterion for each room.
    *   `room_avg_pass`: A list of `True`/`False` values for the **average** illuminance criterion for each room.
    *   `room_pass`: A list of overall `True`/`False` pass statuses for each room.
    *   `room_min_hours`: A list of the minimum hours achieved by any point in each room.
    *   `min_area_pct`: A list of the percentage of area meeting the minimum criterion in each room.
    *   `room_avg_hours`: A list of the hours the spatial average was met for each room.
    *   `avg_area_pct`: A list of the percentage of area meeting the average criterion in each room.
    *   `colored_min_meshes`: A list of meshes colored green/red based on the **minimum** criterion.
    *   `colored_avg_meshes`: A list of meshes colored green/red based on the **average** criterion.

---

#### C. Component 3: UDI/sDA/ASE METRICS READER

1.  **Rename the component** to `Metrics Reader`.
2.  **Right-click** and open the editor. Copy and paste the full script for the **Metrics Reader** component.
3.  **Set up the inputs:**
    *   `json_file_path` (Type hint: `str`)
    *   `grid_names` (Type hint: `str`, **Access: `List`**)

4.  **Understand the outputs:** This component provides standard daylighting metrics:
    *   `message`: A status message for the metrics reader.
    *   `sDA_pct`: **Spatial Daylight Autonomy (sDA 300/50%)**: A list of percentages representing the area that receives at least 300 lux for 50% of occupied hours.
    *   `ASE_pct`: **Annual Sun Exposure (ASE 1000/250h)**: A list of percentages representing the area that receives over 1000 lux for more than 250 hours.
    *   `udi_f_hr`: **UDI-Fallen (Hours)**: A list of the hours the spatial average illuminance is below 100 lux.
    *   `udi_s_hr`: **UDI-Supplementary (Hours)**: A list of the hours the spatial average is between 100 and the UDI minimum lux.
    *   `udi_a_hr`: **UDI-Autonomous (Hours)**: A list of the hours the spatial average is between the UDI minimum and 3000 lux.
    *   `udi_e_hr`: **UDI-Exceeded (Hours)**: A list of the hours the spatial average is above 3000 lux.
    *   `udi_f_pct`, `udi_s_pct`, `udi_a_pct`, `udi_e_pct`: The same UDI bins as above, but reported as a **percentage (%)** of total occupied hours.

### Step 4: Assemble the Workflow in Grasshopper

Connect the components as follows:

1.  Connect all your primary inputs (sliders for thresholds, file paths, grid geometry, etc.) to the **Daylight Analysis RUNNER**.
2.  Connect the `json_file_path` output from the **RUNNER** to the `json_file_path` input of **both** the **BREEAM Reader** and the **Metrics Reader**.
3.  Connect your original `grid_meshes` and `grid_names` to the **BREEAM Reader**.
4.  Connect your original `grid_names` to the **Metrics Reader**.

Your workflow is now ready. To run an analysis, simply toggle the `run_analysis` boolean input on the Runner component to `True`.

### Troubleshooting

*   **"External Script Failed"**: Check the `log` output of the Runner component. It will contain error messages from the external script.
*   **"Python not found"**: Double-check that the `PYTHON_EXECUTABLE_PATH` in the Runner script is correct and that you added Python to your system's PATH during installation.
*   **"ModuleNotFoundError: no module named numpy"**: This means the virtual environment was not activated correctly when you ran `pip install`, or the wrong python executable is being used. Repeat the `pip install` step inside the activated environment.