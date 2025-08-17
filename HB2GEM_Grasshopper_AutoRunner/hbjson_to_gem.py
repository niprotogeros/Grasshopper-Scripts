# -*- coding: utf-8 -*-
"""
hbjson_to_gem.py - HBJSON to GEM converter (stdin-enabled, ASCII-only)

Usage:
  --hbjson "-" reads HBJSON from STDIN; otherwise it is treated as a file path.
  --gem <full_output_path.gem> (required)
  --log <optional_log_file)

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
