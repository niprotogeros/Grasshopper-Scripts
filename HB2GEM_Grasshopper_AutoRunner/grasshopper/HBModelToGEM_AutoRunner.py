# -*- coding: utf-8 -*-
"""
HB Model (in-memory) -> GEM Export (GHPython component, self-contained, ASCII-safe)

Purpose
-------
Exports a Honeybee Model that already exists in Grasshopper memory to an IES-VE
GEM file. Preferred path is in-memory streaming of HBJSON via STDIN to an
external CPython runner (Honeybee/Honeybee-IES). Falls back to using a file
path if you supply _hbjson as a file.

Inputs
------
_hb_model : Generic (preferred). Accepts:
    - HB model object from Honeybee GH
    - a Python dict representing HBJSON
    - an HBJSON string (JSON)
_export   : Bool. True to run the export.
_gemFile  : String. Full path (incl. file name) for the output .gem
pythonPath: String (optional). Path to LBT python.exe; auto-detected if empty.
runnerPath: String (optional). Path to hbjson_to_gem.py; auto-created in TEMP if empty/invalid.
timeout   : Integer (optional). Seconds before abort (default 300).
logFile   : String (optional). Log file to append a success line.
_hbjson   : String (optional). Fallback: either a file path OR a raw JSON string.

Outputs
-------
status  : "OK" / "ERROR" / "READY"
details : Stdout + Stderr from the runner
gemPath : Path to the created GEM on success
"""

import os, sys, json, tempfile, io

from System.Diagnostics import Process, ProcessStartInfo
from Grasshopper.Kernel import GH_RuntimeMessageLevel

# Component metadata
ghenv.Component.Name = "HB Model -> GEM Export (self-contained)"
ghenv.Component.NickName = "HB2GEM"
ghenv.Component.Category = "Honeybee-IES"
ghenv.Component.SubCategory = "Export"
ghenv.Component.Message = "stdin + temp runner"
ghenv.Component.AdditionalHelpFromDocStrings = "1"

# Ensure basestring exists (IronPython)
try:
    basestring
except NameError:
    basestring = str

# ---------- Embedded runner source (ASCII only) ----------
RUNNER_SOURCE_ASCII = r"""# -*- coding: utf-8 -*-
"""
hbjson_to_gem.py - HBJSON to GEM converter (stdin-enabled, ASCII-only)

Usage:
  --hbjson "-" reads HBJSON from STDIN; otherwise it is treated as a file path.
  --gem <full_output_path.gem> (required)
  --log <optional_log_file>

Exit codes:
 0 success
 2 HBJSON input missing/invalid
 3 import error / writer not found
 4 conversion/write failure
"""

import argparse, os, sys, json, pkgutil, importlib, inspect

def discover_writer():
    # Preferred: model_to_ies writes file and returns a path
    try:
        from honeybee_ies.writer import model_to_ies
        def call(model, folder, name):
            return model_to_ies(model, folder=folder, name=name)
        return call, 'honeybee_ies.writer.model_to_ies'
    except Exception:
        pass
    # Fallback: model_to_gem returns a string, so write it to disk
    try:
        from honeybee_ies.writer import model_to_gem
        def call(model, folder, name):
            gem_str = model_to_gem(model)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            path = os.path.join(folder, name + ".gem")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(gem_str)
            return path
        return call, 'honeybee_ies.writer.model_to_gem'
    except Exception:
        pass
    # Last resort: search for any function that mentions "gem" and "model"
    try:
        import honeybee_ies
        for _, mod_name, _ in pkgutil.walk_packages(honeybee_ies.__path__, honeybee_ies.__name__ + "."):
            try:
                mod = importlib.import_module(mod_name)
                for n, obj in inspect.getmembers(mod, inspect.isfunction):
                    if 'gem' in n.lower() and 'model' in n.lower():
                        sig = inspect.signature(obj)
                        if 'model' in sig.parameters:
                            def dynamic_call(model, folder, name, _obj=obj):
                                kwargs = {}
                                ps = inspect.signature(_obj).parameters
                                if 'folder' in ps: kwargs['folder'] = folder
                                if 'name' in ps: kwargs['name'] = name
                                result = _obj(model, **kwargs)
                                if isinstance(result, (str, bytes)):
                                    if not os.path.isdir(folder):
                                        os.makedirs(folder)
                                    path = os.path.join(folder, name + ".gem")
                                    with open(path, 'w', encoding='utf-8') as f:
                                        if isinstance(result, bytes):
                                            result = result.decode('utf-8', 'replace')
                                        f.write(result)
                                    return path
                                return result
                            return dynamic_call, "%s.%s" % (mod_name, n)
            except Exception:
                continue
    except Exception:
        pass
    return None, None

def main():
    p = argparse.ArgumentParser(description="HBJSON (stdin or file) -> GEM via Honeybee-IES")
    p.add_argument("--hbjson", required=True, help="'-' to read HBJSON from STDIN or a file path (HBJSON/HBpkl)")
    p.add_argument("--gem", required=True, help="Full path (including filename) for the output GEM")
    p.add_argument("--log", help="Optional log file to append a success line")
    args = p.parse_args()

    gem_path = os.path.abspath(args.gem)
    log_path = os.path.abspath(args.log) if args.log else None

    try:
        from honeybee.model import Model
    except Exception as e:
        print("ERROR: Cannot import honeybee Model (%s)" % e, file=sys.stderr)
        sys.exit(3)

    # Build model
    if args.hbjson.strip() == "-":
        try:
            raw = sys.stdin.read()
            data = json.loads(raw)
        except Exception as e:
            print("ERROR: Failed to read/parse HBJSON from STDIN (%s)" % e, file=sys.stderr)
            sys.exit(2)
        try:
            model = Model.from_dict(data)
        except Exception as e:
            print("ERROR: Model.from_dict failed (%s)" % e, file=sys.stderr)
            sys.exit(4)
    else:
        hb_path = os.path.abspath(args.hbjson)
        if not os.path.isfile(hb_path):
            print("ERROR: HBJSON file not found: %s" % hb_path, file=sys.stderr)
            sys.exit(2)
        try:
            model = Model.from_file(hb_path)
        except Exception as e:
            print("ERROR: Model.from_file failed (%s)" % e, file=sys.stderr)
            sys.exit(4)

    folder = os.path.dirname(gem_path) or "."
    name = os.path.splitext(os.path.basename(gem_path))[0]
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
    except Exception as e:
        print("ERROR: Cannot create output folder (%s)" % e, file=sys.stderr)
        sys.exit(4)

    writer_fn, writer_name = discover_writer()
    if writer_fn is None:
        print("ERROR: No valid GEM writer function found in honeybee_ies.", file=sys.stderr)
        sys.exit(3)

    try:
        result_path = writer_fn(model, folder, name)
    except Exception as e:
        print("ERROR: Conversion failed (%s)" % e, file=sys.stderr)
        sys.exit(4)

    if not result_path:
        result_path = gem_path
    if not os.path.isfile(result_path) or os.path.getsize(result_path) == 0:
        print("ERROR: GEM file was not created or is empty.", file=sys.stderr)
        sys.exit(4)

    ok_line = "OK: exported GEM file at %s" % result_path
    print(ok_line)
    if log_path:
        try:
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(ok_line + "\n")
        except Exception:
            pass
    sys.exit(0)

if __name__ == "__main__":
    main()
"""

# ---------- Helpers ----------
def _msg(level, text):
    ghenv.Component.AddRuntimeMessage(level, text)

def _is_blank(s):
    try:
        return s is None or str(s).strip() == ""
    except Exception:
        return True

def _find_default_python():
    env_py = os.environ.get('LBT_PYTHON')
    if env_py and os.path.isfile(env_py):
        return env_py
    lbt_home = os.environ.get('LBT_HOME', r"C:\Program Files\ladybug_tools")
    candidate = os.path.join(lbt_home, "python", "python.exe")
    return candidate if os.path.isfile(candidate) else None

def _quote(s):
    s = str(s)
    if '"' in s:
        s = s.replace('"', r'\"')
    return '"' + s + '"'

def _build_args_stdin(py_file, gem_path, log_path):
    args = [_quote(py_file), "--hbjson", "-", "--gem", _quote(gem_path)]
    if not _is_blank(log_path):
        args += ["--log", _quote(log_path)]
    return " ".join(args)

def _build_args_file(py_file, hbjson_path_or_json, gem_path, log_path):
    # If the provided string is a JSON string, we pass it via STDIN anyway.
    if hbjson_path_or_json and str(hbjson_path_or_json).lstrip().startswith("{"):
        return None  # signal to caller to use STDIN instead
    args = [_quote(py_file), "--hbjson", _quote(hbjson_path_or_json), "--gem", _quote(gem_path)]
    if not _is_blank(log_path):
        args += ["--log", _quote(log_path)]
    return " ".join(args)

def _materialize_runner_to_temp():
    """Write the runner script to TEMP with UTF-8 encoding, return its path or error."""
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, "hbjson_to_gem.py")
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(RUNNER_SOURCE_ASCII)
        return path, None
    except Exception as e:
        return None, "Failed to write runner to TEMP: {0}".format(e)

def _serialize_obj_to_hbjson_text(obj):
    """Try to produce HBJSON text from a variety of possible GH inputs."""
    # 1) Already a string (must be JSON)
    try:
        if isinstance(obj, basestring):
            s = obj.strip()
            if s.startswith("{") and s.endswith("}"):
                json.loads(s)  # sanity check
                return s, None
    except Exception:
        pass
    # 2) Plain Python dict (or dict-like)
    try:
        if hasattr(obj, "keys"):  # very generic check
            return json.dumps(obj), None
    except Exception:
        pass
    # 3) .NET or wrapper objects with serialization methods
    probe_methods = [
        "ToJson", "ToJSON", "ToJsonString", "ToJsonText",
        "ToHBJSON", "ToDict", "ToDictionary", "ToPython",
        "ToString"
    ]
    for m in probe_methods:
        try:
            if hasattr(obj, m):
                res = getattr(obj, m)
                res = res() if callable(res) else res
                try:
                    if hasattr(res, "keys"):
                        return json.dumps(res), None
                except Exception:
                    pass
                if isinstance(res, basestring):
                    s = res.strip()
                    try:
                        json.loads(s)
                        return s, None
                    except Exception:
                        continue
        except Exception:
            pass
    return None, ("Could not serialize the provided HB model to HBJSON text. "
                  "Try feeding a Honeybee 'Dump/To JSON' into _hb_model or use _hbjson as a file path or JSON string.")

# ---------- Outputs ----------
status = "READY"
details = ""
gemPath = None

# Grab optionals safely
pythonPath_val = globals().get("pythonPath", None)
runnerPath_val = globals().get("runnerPath", None)
timeout_val    = globals().get("timeout", None)
logFile_val    = globals().get("logFile", None)
_hbjson_val    = globals().get("_hbjson", None)

# ---------- Main ----------
using_stdin = False
stdin_payload = None

if globals().get("_export", False):
    if _is_blank(globals().get("_gemFile", None)):
        _msg(GH_RuntimeMessageLevel.Error, "Input _gemFile (output GEM path) is required.")
        status = "ERROR"
    else:
        gem_path = str(globals().get("_gemFile")).strip()

    if status != "ERROR":
        py_path = None if (pythonPath_val is None or _is_blank(pythonPath_val)) else str(pythonPath_val).strip()
        if not py_path:
            py_path = _find_default_python()
        if not py_path or not os.path.isfile(py_path):
            _msg(GH_RuntimeMessageLevel.Error, "Ladybug Tools Python not found. Provide pythonPath or set LBT_HOME/LBT_PYTHON.")
            status = "ERROR"

    if status != "ERROR":
        out_dir = os.path.dirname(gem_path)
        if out_dir and not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir)
            except Exception as e:
                _msg(GH_RuntimeMessageLevel.Error, "Failed to create output folder: {0}".format(e))
                status = "ERROR"

    run_path = None if (runnerPath_val is None or _is_blank(runnerPath_val)) else str(runnerPath_val).strip()
    if status != "ERROR":
        if not run_path or not os.path.isfile(run_path):
            auto_path, err = _materialize_runner_to_temp()
            if err:
                _msg(GH_RuntimeMessageLevel.Error, err + " (Alternatively set a valid runnerPath.)")
                status = "ERROR"
            else:
                run_path = auto_path
                _msg(GH_RuntimeMessageLevel.Remark, "Runner created at TEMP: {0}".format(run_path))

    wait_seconds = 300
    if status != "ERROR":
        try:
            if timeout_val is not None:
                wait_seconds = int(timeout_val)
                if wait_seconds <= 0:
                    wait_seconds = 300
        except (ValueError, TypeError):
            wait_seconds = 300

    hbjson_path_or_json = None
    if status != "ERROR":
        hb_model_val = globals().get("_hb_model", None)
        if hb_model_val is not None and not _is_blank(hb_model_val):
            hbjson_text, err = _serialize_obj_to_hbjson_text(hb_model_val)
            if err:
                if _hbjson_val and not _is_blank(_hbjson_val):
                    hbjson_path_or_json = str(_hbjson_val).strip()
                else:
                    _msg(GH_RuntimeMessageLevel.Error, err)
                    status = "ERROR"
            else:
                stdin_payload = hbjson_text
                using_stdin = True
        elif _hbjson_val and not _is_blank(_hbjson_val):
            hbjson_path_or_json = str(_hbjson_val).strip()
            if hbjson_path_or_json.lstrip().startswith("{"):
                stdin_payload = hbjson_path_or_json
                using_stdin = True
        else:
            _msg(GH_RuntimeMessageLevel.Error, "Provide _hb_model (preferred) or _hbjson (path or JSON string).")
            status = "ERROR"

    if status != "ERROR":
        psi = ProcessStartInfo()
        psi.FileName = py_path
        log_arg = None if (logFile_val is None or _is_blank(logFile_val)) else str(logFile_val).strip()

        if using_stdin:
            psi.Arguments = " ".join([_quote(run_path), "--hbjson", "-", "--gem", _quote(gem_path)] + (["--log", _quote(log_arg)] if log_arg else []))
        else:
            if hbjson_path_or_json and hbjson_path_or_json.lstrip().startswith("{"):
                stdin_payload = hbjson_path_or_json
                using_stdin = True
                psi.Arguments = " ".join([_quote(run_path), "--hbjson", "-", "--gem", _quote(gem_path)] + (["--log", _quote(log_arg)] if log_arg else []))
            else:
                if not os.path.isfile(hbjson_path_or_json):
                    _msg(GH_RuntimeMessageLevel.Error, "Fallback _hbjson file not found: {0}".format(hbjson_path_or_json))
                    status = "ERROR"
                psi.Arguments = " ".join([_quote(run_path), "--hbjson", _quote(hbjson_path_or_json), "--gem", _quote(gem_path)] + (["--log", _quote(log_arg)] if log_arg else []))

        if status != "ERROR":
            psi.UseShellExecute = False
            psi.RedirectStandardOutput = True
            psi.RedirectStandardError = True
            psi.CreateNoWindow = True
            psi.WorkingDirectory = os.path.dirname(gem_path) if os.path.dirname(gem_path) else os.getcwd()
            psi.RedirectStandardInput = using_stdin

            proc = None
            try:
                proc = Process()
                proc.StartInfo = psi
                if not proc.Start():
                    status = "ERROR"
                    details = "Failed to start external Python process."
                    _msg(GH_RuntimeMessageLevel.Error, details)
                else:
                    if using_stdin:
                        try:
                            sw = proc.StandardInput
                            sw.Write(stdin_payload)
                            sw.Close()
                        except Exception as e:
                            status = "ERROR"
                            details = "Failed to send HBJSON via STDIN: {0}".format(e)
                            _msg(GH_RuntimeMessageLevel.Error, details)

                    if status != "ERROR":
                        if not proc.WaitForExit(wait_seconds * 1000):
                            try:
                                proc.Kill()
                            except Exception:
                                pass
                            status = "ERROR"
                            details = "Process timed out after {0} seconds. Increase 'timeout' for large models.".format(wait_seconds)
                            _msg(GH_RuntimeMessageLevel.Error, details)
                        else:
                            try:
                                stdout_txt = proc.StandardOutput.ReadToEnd()
                            except Exception:
                                stdout_txt = ""
                            try:
                                stderr_txt = proc.StandardError.ReadToEnd()
                            except Exception:
                                stderr_txt = ""
                            details = (stdout_txt or "") + (("\nErrors:\n" + stderr_txt) if stderr_txt else "")
                            if proc.ExitCode != 0:
                                status = "ERROR"
                                _msg(GH_RuntimeMessageLevel.Error, "GEM export failed (exit code {0}). See 'details'.".format(proc.ExitCode))
                            else:
                                status = "OK"
                                gemPath = gem_path
                                _msg(GH_RuntimeMessageLevel.Remark, "HB model exported to GEM:\n{0}".format(gem_path))
            except Exception as e:
                status = "ERROR"
                details = "Failed to execute external process: {0}".format(e)
                _msg(GH_RuntimeMessageLevel.Error, details)
            finally:
                if proc is not None:
                    try:
                        if not proc.HasExited:
                            proc.Kill()
                    except Exception:
                        pass
else:
    _msg(GH_RuntimeMessageLevel.Remark, "Export flag not set. Set _export to True to perform export.")
    status = "READY"
