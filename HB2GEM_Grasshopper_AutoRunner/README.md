# HBModelToGEM (Auto-Runner Variant)

Export a Honeybee (HB) model **directly from Grasshopper memory** to an IES-VE **.GEM** file — no temporary HBJSON file required. This variant of the GHPython component **auto-creates** the command-line runner in your **%TEMP%** directory when `runnerPath` is left blank, so you don’t need to manage the runner script manually (you can still point to a repo copy if you prefer).

---

## Repository structure

- `grasshopper/HBModelToGEM_AutoRunner.py` — GHPython component code (auto-runner).
- `hbjson_to_gem.py` — runner script (included for reference or explicit use).
- `README.md` — this guide.

---

## Requirements (install before you start)

- **Windows 10/11 (64-bit)** with write access to the output folder.
- **Rhino 7 (64-bit)** with **Grasshopper** and the built-in **GHPython (IronPython 2.7)** component.
- **Ladybug Tools ≥ 1.8** (standard installer)
  - Bundled CPython: `C:\Program Files\ladybug_tools\python\python.exe`
  - Installs the core Honeybee stack used by the runner.
- **Honeybee-IES** installed in the **same** Ladybug Tools Python environment.
- *(Optional)* **IESVE** to open/inspect `.gem` files (not required to export).

### Verify your installation (recommended)

Run these **exactly** with the Ladybug Tools Python (note the quotes):

```bat
"C:\Program Files\ladybug_tools\python\python.exe" -c "import honeybee, honeybee_ies; print('honeybee:', honeybee.__version__); print('honeybee_ies:', honeybee_ies.__version__)"
```

- If both imports succeed and versions print, you’re good.
- If `honeybee_ies` fails to import, install/repair it:

```bat
"C:\Program Files\ladybug_tools\python\python.exe" -m pip install --upgrade pip
"C:\Program Files\ladybug_tools\python\python.exe" -m pip install --upgrade honeybee-ies
```

> If LBT is installed elsewhere, point the Grasshopper input **`pythonPath`** to that `python.exe`.

---

## Quick start (Grasshopper)

1. Drop a **Python** component on the Grasshopper canvas.
2. **Manage Inputs…** and add/rename:
   - `_hb_model` (Generic) — HB model object **or** HBJSON string/dict.
   - `_export` (Boolean) — set **True** to run.
   - `_gemFile` (String) — full path to output `.gem`.
   - `pythonPath` (String, optional) — path to LBT `python.exe`.
   - `runnerPath` (String, optional) — leave empty to auto-create in `%TEMP%`; set to a file if you want to use a repo copy.
   - `timeout` (Integer, optional) — seconds; default 300.
   - `logFile` (String, optional) — path to a log file to append success line.
   - `_hbjson` (String, optional) — fallback path or raw JSON string.
3. **Manage Outputs…** and add/rename:
   - `status` — "OK" / "ERROR" / "READY".
   - `details` — stdout + stderr text from the runner.
   - `gemPath` — the written `.gem` path on success.
4. Open `grasshopper/HBModelToGEM_AutoRunner.py`, copy all text, and paste it into the GHPython editor.

---

## Using the component

### Preferred (in-memory)

- Wire your Honeybee **Model object** to `_hb_model`.
- Alternatively, wire a **JSON string** from a “Dump/To JSON” HB component to `_hb_model`.
- Set `_gemFile` to your target file (e.g., `C:\HB\model.gem`).
- Toggle `_export` to **True**.

### Fallback (file path or raw JSON)

- Provide `_hbjson` as **either**:
  - an HBJSON/HBpkl **file path**, or
  - a raw **HBJSON string**.  
  The component auto-detects and will stream JSON via STDIN when appropriate.

### Runner handling

- If `runnerPath` is **empty/invalid**, the component writes a fresh runner to `%TEMP%` (ASCII-only source, UTF-8 file) and uses it automatically.
- If you prefer version control, put `hbjson_to_gem.py` in your repo and set `runnerPath` to it.

---

## Input & output reference (Grasshopper)

**Inputs**
- `_hb_model` — HB model object **or** HBJSON dict/string (preferred path).
- `_export` — Boolean trigger.
- `_gemFile` — Full output path (including filename) for `.gem`.
- `pythonPath` — Override path to LBT `python.exe` (auto-detected otherwise).
- `runnerPath` — Leave blank to auto-create in `%TEMP%`; or set to this repo’s `hbjson_to_gem.py`.
- `timeout` — Seconds before kill; increase for large models (e.g., 900).
- `logFile` — Optional log path; appends one-line success.
- `_hbjson` — Fallback path to HBJSON/HBpkl **or** raw HBJSON string.

**Outputs**
- `status` — "OK" on success; "ERROR" on failure; "READY" when waiting.
- `details` — Combined stdout/stderr from the runner for diagnostics.
- `gemPath` — Final GEM file path when successful.

---

## Troubleshooting

- **Runner script not found / writing error**  
  This variant auto-creates the runner in `%TEMP%` using ASCII-only content and UTF-8 encoding. If your environment blocks writing to `%TEMP%`, set `runnerPath` to a location you control (e.g., inside your repo).

- **“Could not serialize the provided HB model …”**  
  Feed a **Honeybee “Dump/To JSON”** output (JSON string) into `_hb_model`, or provide `_hbjson` as a file path/JSON string.

- **Timeout**  
  Increase `timeout` for large models (e.g., 900–1800 seconds). Ensure you have write permissions to the output folder.

- **`honeybee_ies` missing**  
  Install it in the LBT Python as shown above. Verify imports with the one-liner.

- **Wrong Python**  
  Set `pythonPath` to your Ladybug Tools `python.exe` if it isn't at the default.

- **Permissions / antivirus**  
  Some environments block launching external processes or writing to `%TEMP%`. Choose writable locations and check IT policies.

---

## Version notes

- This project targets **Rhino 7 / IronPython 2.7**.  
  In **Rhino 8** (Python 3), you can call Honeybee/Honeybee-IES directly in-process and skip the runner.

---

## Acknowledgements

- Built on the outstanding work of **Ladybug Tools** and **Honeybee-IES**.

---

## License

Choose a license for your repository (e.g., MIT). If you’d like, add a `LICENSE` file later.
