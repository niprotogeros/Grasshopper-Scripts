"""
Send to IESVE (GEM) — GH Python component
Inputs:
    run (bool): Trigger to execute (True to run)
    gem_path (text): Full path to the .gem file to import
    ve_exe (text): Full path to VE.exe (IESVE)
    ahk_path (text, optional): Path to AutoHotkey script (iesve_import_gem.ahk)

Outputs:
    status (text): Status / diagnostic messages

Hover help: This component launches IESVE and drives the Import GEM UI via AutoHotkey v2.
"""

import System
import clr
import os
import time
from System.Diagnostics import Process, ProcessStartInfo

# ------------- Helper: configure nice names/tooltips on first run -------------
try:
    import scriptcontext as sc
    if not sc.sticky.get("SendToIESVE_Configured", False):
        comp = ghenv.Component

        comp.Name = "Send to IESVE (GEM)"
        comp.NickName = "SendToIESVE"
        comp.Description = ("Launch IESVE and import a .GEM file automatically via AutoHotkey v2.\n"
                            "Provide full paths for VE.exe and the GEM file.")

        # Input names & descriptions
        ip = comp.Params.Input
        ip[0].NickName = "run"
        ip[0].Name = "Run"
        ip[0].Description = "Boolean trigger. Set to True to execute."

        ip[1].NickName = "gem"
        ip[1].Name = "GEM Path"
        ip[1].Description = "Full path to the .gem file you exported."

        ip[2].NickName = "ve"
        ip[2].Name = "VE.exe Path"
        ip[2].Description = "Full path to IESVE executable (VE.exe)."

        ip[3].NickName = "ahk"
        ip[3].Name = "AHK Script Path"
        ip[3].Description = "Path to iesve_import_gem.ahk (AutoHotkey v2). If empty, we try a default."

        # Output
        op = comp.Params.Output
        op[0].NickName = "status"
        op[0].Name = "Status"
        op[0].Description = "Status text / diagnostics."

        comp.Message = "Ready"
        sc.sticky["SendToIESVE_Configured"] = True
except Exception as _e:
    pass

# ------------- Validation -------------
def fail(msg):
    ghenv.Component.Message = "Error"
    return msg

status = ""

if not run:
    ghenv.Component.Message = "Idle"
    status = "Set 'run' to True to execute."
else:
    # Validate GEM path
    if not gem_path or not os.path.isfile(gem_path):
        status = fail("Invalid GEM path: {}".format(gem_path))
    elif not ve_exe or not os.path.isfile(ve_exe):
        status = fail("Invalid VE.exe path: {}".format(ve_exe))
    else:
        # Determine AutoHotkey v2 executable and script path
        # Common AHK v2 install path (adjust if needed)
        ahk_exe_candidates = [
            r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
            r"C:\Program Files\AutoHotkey\AutoHotkey64.exe",
            r"C:\Program Files\AutoHotkey\AutoHotkey.exe"
        ]
        ahk_exe = None
        for c in ahk_exe_candidates:
            if os.path.isfile(c):
                ahk_exe = c
                break

        if ahk_path and os.path.isfile(ahk_path):
            ahk_script = ahk_path
        else:
            # Try a sensible default under C:\Tools
            ahk_script = r"C:\Tools\iesve_import_gem.ahk"

        if ahk_exe is None:
            status = fail("AutoHotkey v2 not found. Install from https://www.autohotkey.com/ and update the path in this component if needed.")
        elif not os.path.isfile(ahk_script):
            status = fail("AHK script not found: {}. Place iesve_import_gem.ahk and point to it.".format(ahk_script))
        else:
            try:
                # Launch VE if not already running
                procs = Process.GetProcessesByName("VE")
                if procs.Length == 0:
                    psi = ProcessStartInfo(ve_exe)
                    psi.UseShellExecute = True
                    Process.Start(psi)
                    # give VE a moment to show its window
                    time.sleep(2.0)

                # Start AHK to drive the import (pass GEM path as the sole argument)
                psi2 = ProcessStartInfo()
                psi2.FileName = ahk_exe
                psi2.Arguments = u'"{}" "{}"'.format(ahk_script, gem_path)
                psi2.UseShellExecute = False
                p = Process.Start(psi2)

                ghenv.Component.Message = "Importing..."
                status = "Launched IESVE and sent import command for:\n{}".format(gem_path)
            except Exception as e:
                status = fail("Launch/automation failed: {}".format(e))

# GH outputs
status_out = status
