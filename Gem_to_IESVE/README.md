# Grasshopper → IESVE (GEM) One-Click Import

This mini-tool lets you click a single button in **Rhino 7 / Grasshopper** to:
1. Launch **IESVE** (VE.exe), and
2. Run **Import GEM** to load the `.gem` you exported from Honeybee/Ladybug (or any source).

It uses a small **GHPython** component plus a lightweight **AutoHotkey v2** script that presses the same menu keys you would use.

---

## Repo Structure

```
gh-send-to-iesve-gem/
├─ grasshopper/
│  └─ GHPython_SendToIESVE.py        # Paste this into a GH Python component
├─ scripts/
│  └─ iesve_import_gem.ahk           # AutoHotkey v2 UI automation
└─ LICENSE
```

---

## Prerequisites

- **Rhino 7 + Grasshopper**
- **IESVE** installed (you must know your `VE.exe` path)
- **AutoHotkey v2** (download from the official site and install)
  - Typical path: `C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe`

---

## Setup (once)

1. Copy `scripts/iesve_import_gem.ahk` to a stable location, e.g. `C:\Tools\iesve_import_gem.ahk`.
2. Open **Grasshopper** in Rhino.
3. Drop a **GHPython** component on the canvas.
4. Double‑click it, delete the template code, and paste the contents of `grasshopper/GHPython_SendToIESVE.py`.
5. Add four inputs to the component in this order and set their types to **Text** (except the first which is **Boolean**):
   - `run` (Boolean)
   - `gem_path` (Text)
   - `ve_exe` (Text)
   - `ahk_path` (Text, optional)
6. Add one output named `status` (Text).  
   The script will auto‑label inputs/outputs and add hover tooltips.

---

## Usage (every time)

1. Make sure your workflow exported a fresh `.gem` file.
2. In the GH Python component:
   - `run`: set to **True** to trigger the action.
   - `gem_path`: absolute path to your `.gem` file.
   - `ve_exe`: absolute path to `VE.exe` (e.g. `C:\Program Files\IES\VE 2025\apps\VE.exe`).
   - `ahk_path` (optional): if omitted, the script looks for `C:\Tools\iesve_import_gem.ahk`.
3. When `run=True`, it will:
   - Launch IESVE if it isn’t already running.
   - Call AutoHotkey, which switches to **ModelIT**, runs **File → Import → GEM File...**,
     selects your `.gem`, and accepts the **Quarantine** dialog (if shown).

> Tip: If your VE build uses different menu accelerators, open the menus once with the **Alt** key to see the underlined letters, then edit the three `Send(...)` lines in `iesve_import_gem.ahk` accordingly.

---

## Troubleshooting

- **AHK not found** — Install AutoHotkey v2 and update the path inside the GH Python script if needed (search for `ahk_exe_candidates`).
- **Script can’t find the AHK file** — Move the `.ahk` to `C:\Tools\iesve_import_gem.ahk` or set `ahk_path` explicitly.
- **No File Open dialog** — Your VE menu keys differ. Edit the `Send("!f")`, `Send("i")`, `Send("g")` lines in the `.ahk` script.
- **Quarantine window title differs** — Change `"Quarantine"` in the `.ahk` to the exact dialog title you see.
- **Security/permissions** — Run Rhino as a normal user (not elevated) and make sure AutoHotkey is allowed by antivirus/AppLocker policies.

---

## Versioning & License

- Suggested repo name: **gh-send-to-iesve-gem**
- License: MIT (see `LICENSE`)

If you post this on GitHub, include a screenshot/gif in the README showing the GH canvas with the component and the import happening.
