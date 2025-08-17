# Clipping Plane Manager (Rhino 7 + Grasshopper)

Manage a single **Rhino Clipping Plane** inside a dedicated layer named **"Clipping Plane"** directly from a Grasshopper script component.

## Features
- Finds/creates a Rhino layer **"Clipping Plane"** (unlocked & visible).
- Keeps **exactly one** clipping plane in that layer (deletes extras).
- If none exists and **Create = True**, creates one on **World XY** near the origin.
- Moves/rotates the kept clipping plane to match the **input Plane P**.
- Binds the plane to **all current viewports** (re-run after opening new views).
- Includes **component and socket tooltips** (GhPython version).

Tested with **Rhino 7** (Windows) + **Grasshopper**. IronPython 2.7 for GhPython.

---

## Quick Start (GhPython)
1. In Grasshopper, drop a **GhPython** component.
2. Right‑click it → **Type hints**: set `P` to `Plane`. (Optional, but recommended)
3. Add inputs/outputs:
   - Inputs: `P` *(Plane)*, `Create` *(Boolean)*, `Size` *(Number)*
   - Outputs: `ClipId` *(Guid)*, `Status` *(Text)*
4. Open the GhPython editor and paste the contents of:  
   `src/ghpython/ClipPlaneManager_GhPython.py`
5. Press **OK** and run.

### Inputs
- **P** (Plane): Target plane to align the clipping plane to.
- **Create** (Boolean): If `True` and none exists, create one on World XY near the origin.
- **Size** (Number): Width/height of the clipping-plane widget (clipping effect is infinite).

### Outputs
- **ClipId** (Guid): The GUID of the kept clipping plane (empty if none exists).
- **Status** (Text): Human-readable status of the operation.

> Tip: “Size” affects the visible plane widget only; clipping itself is infinite in that plane.

---

## Alternative: C# Script Component
If you prefer C#, use the code in `src/csharp/ClipPlaneManager_CSharp.cs` with a C# Script component.  
Inputs/outputs are the same (`P`, `Create`, `Size` → `ClipId`, `Status`).

---

## Folder Structure
```
ClipPlaneManager_GH/
├─ src/
│  ├─ ghpython/
│  │  └─ ClipPlaneManager_GhPython.py
│  └─ csharp/
│     └─ ClipPlaneManager_CSharp.cs
├─ LICENSE
├─ README.md
├─ CHANGELOG.md
└─ .gitignore
```

---

## License
This project is released under the MIT License. See [LICENSE](LICENSE).

