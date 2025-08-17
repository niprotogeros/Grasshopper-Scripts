"""
Post-process Honeybee Annual Daylight results from a folder.
This script reads raw hourly illuminance data (.npy files) and calculates
BREEAM, UDI, sDA, and ASE metrics.

USAGE (6 arguments required):
  python post_process_daylight_all_grids.py \
         <results_folder> <min_lux> <min_hours_req> \
         <avg_lux> <avg_hours_req> <udi_min_lux>

Output:
  Writes daylight_summary.json inside <results_folder>
"""

import sys
import json
from pathlib import Path
import numpy as np

def find_npy_files(root_path: Path):
    """Finds all .npy result files within the simulation folder."""
    npy_folder = root_path / 'results' / '__static_apertures__' / 'default' / 'total'
    
    if not npy_folder.is_dir():
        raise FileNotFoundError(
            f"Could not find the NumPy results folder at: {npy_folder}\n"
            "Please ensure the simulation ran correctly and created .npy files."
        )

    npy_files = list(npy_folder.glob('*.npy'))
    if not npy_files:
        raise FileNotFoundError(f"No .npy files found in {npy_folder}")
    
    return npy_files

def main():
    if len(sys.argv) != 7:
        sys.exit(
            "USAGE:\n  python post_process_daylight_all_grids.py "
            "<results_folder> <min_lux> <min_hours_req> <avg_lux> "
            "<avg_hours_req> <udi_min_lux>"
        )

    try:
        results_root = Path(sys.argv[1]).expanduser().resolve()
        min_lux = float(sys.argv[2])
        min_h_req = int(sys.argv[3])
        avg_lux = float(sys.argv[4])
        avg_h_req = int(sys.argv[5])
        udi_min_lux = float(sys.argv[6]) # New input
    except (ValueError, IndexError):
        sys.exit("ERROR: Invalid arguments provided.")

    try:
        npy_files = find_npy_files(results_root)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}")

    room_results = []
    for npy_file in npy_files:
        room_label = npy_file.stem
        
        try:
            arr = np.load(npy_file)
        except Exception as e:
            print(f"Warning: Could not read {npy_file}. Skipping. Error: {e}")
            continue
            
        # Get shape of the data array
        total_points, total_hours = arr.shape
        if total_points == 0 or total_hours == 0:
            print(f"Warning: Empty data array in {npy_file}. Skipping.")
            continue

        # --- BREEAM MINIMUM POINT ANALYSIS ---
        hours_above_min_lux = (arr >= min_lux).sum(axis=1)
        min_hours_in_room = int(hours_above_min_lux.min())
        min_pass = min_hours_in_room >= min_h_req
        points_passing_min = (hours_above_min_lux >= min_h_req).sum()
        min_area_pct = round((points_passing_min / total_points) * 100, 2)
        
        # --- BREEAM SPATIAL AVERAGE ANALYSIS ---
        hourly_spatial_average = arr.mean(axis=0)
        avg_hours_in_room = int((hourly_spatial_average >= avg_lux).sum())
        avg_pass = avg_hours_in_room >= avg_h_req
        hours_above_avg_lux = (arr >= avg_lux).sum(axis=1)
        points_passing_avg = (hours_above_avg_lux >= avg_h_req).sum()
        avg_area_pct = round((points_passing_avg / total_points) * 100, 2)

        # --- sDA (Spatial Daylight Autonomy) ANALYSIS ---
        # % of area receiving at least 300 lux for 50% of hours
        sda_hour_threshold = total_hours * 0.5
        hours_above_300_lux = (arr >= 300).sum(axis=1)
        points_passing_sda = (hours_above_300_lux >= sda_hour_threshold).sum()
        sDA_pct = round((points_passing_sda / total_points) * 100, 2)

        # --- ASE (Annual Sun Exposure) ANALYSIS ---
        # % of area receiving > 1000 lux for > 250 hours
        # Note: ASE specifies "direct sunlight", but here we use total illuminance
        # as is common practice in Honeybee ASE recipes.
        hours_above_1000_lux = (arr > 1000).sum(axis=1)
        points_passing_ase = (hours_above_1000_lux > 250).sum()
        ASE_pct = round((points_passing_ase / total_points) * 100, 2)

        # --- UDI (Useful Daylight Illuminance) ANALYSIS ---
        # Based on the spatial average illuminance for each hour
        
        # Calculate hours in each bin
        udi_f_hours = int((hourly_spatial_average < 100).sum())
        udi_e_hours = int((hourly_spatial_average > 3000).sum())
        udi_a_hours = int(((hourly_spatial_average >= udi_min_lux) & (hourly_spatial_average <= 3000)).sum())

        udi_s_hours = 0
        if udi_min_lux > 100:
            udi_s_hours = int(((hourly_spatial_average >= 100) & (hourly_spatial_average < udi_min_lux)).sum())
            
        # Calculate percentage of occupied hours in each bin
        udi_f_pct = round((udi_f_hours / total_hours) * 100, 2)
        udi_s_pct = round((udi_s_hours / total_hours) * 100, 2)
        udi_a_pct = round((udi_a_hours / total_hours) * 100, 2)
        udi_e_pct = round((udi_e_hours / total_hours) * 100, 2)


        room_results.append({
            "room_label": room_label,
            "n_points": total_points,
            "total_hours": total_hours,
            # BREEAM
            "min_hours_achieved": min_hours_in_room,
            "min_pass": min_pass,
            "avg_hours_achieved": avg_hours_in_room,
            "avg_pass": avg_pass,
            "room_pass": min_pass and avg_pass,
            "min_area_pct": min_area_pct,
            "avg_area_pct": avg_area_pct,
            # sDA and ASE
            "sDA_300_50_pct": sDA_pct,
            "ASE_1000_250_pct": ASE_pct,
            # UDI Hours
            "udi_f_hours (<100lx)": udi_f_hours,
            "udi_s_hours (100-min)": udi_s_hours,
            "udi_a_hours (min-3000lx)": udi_a_hours,
            "udi_e_hours (>3000lx)": udi_e_hours,
            # UDI Percentages
            "udi_f_pct (<100lx)": udi_f_pct,
            "udi_s_pct (100-min)": udi_s_pct,
            "udi_a_pct (min-3000lx)": udi_a_pct,
            "udi_e_pct (>3000lx)": udi_e_pct
        })
    
    # --- Create the final JSON summary ---
    if room_results:
        building_pass = all(r["room_pass"] for r in room_results)
        worst_room_obj = min(room_results, key=lambda r: r["min_hours_achieved"])
        worst_room_label = worst_room_obj["room_label"]
    else:
        building_pass = False
        worst_room_label = "N/A"

    output_data = {
        "summary": {
            "overall_building_pass": building_pass,
            "overall_worst_room_label": worst_room_label,
            "total_rooms_analysed": len(room_results)
        },
        "parameters": {
            "min_lux": min_lux, "min_hours_req": min_h_req,
            "avg_lux": avg_lux, "avg_hours_req": avg_h_req,
            "udi_min_lux": udi_min_lux
        },
        "rooms": room_results
    }

    json_path = results_root / "daylight_summary.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"[OK] Analysed {len(room_results)} rooms from .npy files -> {json_path}")
    except IOError as e:
        sys.exit(f"ERROR: Could not write summary file to {json_path}. Details: {e}")

if __name__ == "__main__":
    main()