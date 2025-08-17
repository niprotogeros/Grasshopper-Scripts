"""
Clipping Plane Manager (GhPython)

• Finds a Rhino layer named “Clipping Plane”. If missing, it creates it (unlocked/visible).
• Keeps EXACTLY ONE clipping plane in that layer:
    - If none and Create=True → makes one on World XY near the origin.
    - If multiple exist → deletes extras and keeps one.
• Aligns the kept clipping plane to the input Plane P (move + rotate).
• Binds the plane to all current viewports (re-run if you open new views).

Tip: “Size” only affects the plane widget extents; clipping is infinite in that plane.
"""

import System
import Rhino
import scriptcontext as sc

# ---------- UI / Tooltips ----------
try:
    comp = ghenv.Component
    # Short label shown on the component face (helps at-a-glance)
    comp.NickName = "ClipPlane Manager"
    comp.Message = "Manages a single clipping plane in layer 'Clipping Plane'"

    # Input names & hover tooltips
    pin = comp.Params.Input
    if len(pin) >= 1:
        pin[0].Name = "Plane"
        pin[0].NickName = "P"
        pin[0].Description = "Target plane. The (kept) clipping plane will be moved/rotated to match this plane."
    if len(pin) >= 2:
        pin[1].Name = "Create if missing"
        pin[1].NickName = "Create"
        pin[1].Description = "Set True to create a clipping plane on World XY near the origin if none exists in the 'Clipping Plane' layer."
    if len(pin) >= 3:
        pin[2].Name = "Widget size"
        pin[2].NickName = "Size"
        pin[2].Description = "Width/height of the clipping-plane widget in model units (clipping effect itself is infinite)."

    # Output names & hover tooltips
    pout = comp.Params.Output
    if len(pout) >= 1:
        pout[0].Name = "Clipping Plane Id"
        pout[0].NickName = "ClipId"
        pout[0].Description = "GUID of the single clipping plane kept in the 'Clipping Plane' layer (empty if none)."
    if len(pout) >= 2:
        pout[1].Name = "Status"
        pout[1].NickName = "Status"
        pout[1].Description = "Human-readable status message describing what the component did."
except:
    pass
# ---------- end UI / Tooltips ----------

def ensure_layer(doc, name):
    idx = doc.Layers.Find(name, True)
    if idx < 0:
        l = Rhino.DocObjects.Layer()
        l.Name = name
        l.IsLocked = False
        l.IsVisible = True
        idx = doc.Layers.Add(l)
    else:
        lyr = doc.Layers[idx]
        if lyr.IsDeleted:
            lyr.IsDeleted = False
            doc.Layers.Modify(lyr, idx, True)
        if lyr.IsLocked:
            lyr.IsLocked = False
            doc.Layers.Modify(lyr, idx, True)
    return idx

def all_viewport_ids(doc):
    views = doc.Views.GetViewList(True, True)
    ids = []
    if views:
        for v in views:
            try:
                ids.append(v.ActiveViewportID)
            except:
                pass
    if len(ids) == 0 and doc.Views.ActiveView:
        ids.append(doc.Views.ActiveView.ActiveViewportID)
    # distinct
    uniq = []
    for i in ids:
        if i not in uniq:
            uniq.append(i)
    return uniq

def get_clips_in_layer(doc, layer_name):
    ros = doc.Objects.FindByLayer(layer_name)
    if not ros: return []
    return [o for o in ros if isinstance(o, Rhino.DocObjects.ClippingPlaneObject)]

def create_clip(doc, plane, size, layer_index, vps):
    if size is None or size <= 0.0: size = 1000.0
    cid = doc.Objects.AddClippingPlane(plane, size, size, vps)
    if cid == System.Guid.Empty: return System.Guid.Empty
    attr = Rhino.DocObjects.ObjectAttributes()
    attr.LayerIndex = layer_index
    doc.Objects.ModifyAttributes(cid, attr, True)
    return cid

def main(P, Create, Size):
    ClipId = System.Guid.Empty
    Status = ""
    doc = Rhino.RhinoDoc.ActiveDoc
    if doc is None:
        return ClipId, "No active Rhino document."

    # Ensure we operate on the Rhino doc (not GH temp doc)
    prevdoc = sc.doc
    sc.doc = doc
    try:
        layer_index = ensure_layer(doc, "Clipping Plane")
        vps = all_viewport_ids(doc)

        clips = get_clips_in_layer(doc, "Clipping Plane")

        if len(clips) == 0 and Create:
            nid = create_clip(doc, Rhino.Geometry.Plane.WorldXY, Size, layer_index, vps)
            if nid == System.Guid.Empty:
                return ClipId, "Failed to create clipping plane."
            clips = get_clips_in_layer(doc, "Clipping Plane")

        # Keep exactly one
        if len(clips) > 1:
            clips.sort(key=lambda c: str(c.Id))  # stable heuristic
            for i in range(1, len(clips)):
                doc.Objects.Delete(clips[i], True)
            clips = [clips[0]]

        if len(clips) == 0:
            return ClipId, "No clipping plane in layer 'Clipping Plane'. Set Create=True to make one on World XY."

        clip = clips[0]
        cgeom = clip.ClippingPlaneGeometry

        # Get current plane robustly
        try:
            ok, current = cgeom.TryGetPlane()
            if not ok:
                current = cgeom.Plane
        except:
            current = cgeom.Plane

        xform = Rhino.Geometry.Transform.PlaneToPlane(current, P)
        ok = doc.Objects.Transform(clip.Id, xform, True)
        if not ok:
            # Replace if transform failed
            doc.Objects.Delete(clip, True)
            nid = create_clip(doc, P, Size, layer_index, vps)
            if nid == System.Guid.Empty:
                return ClipId, "Failed to reposition; could not recreate."
            ClipId = nid
            doc.Views.Redraw()
            return ClipId, "Recreated clipping plane at input plane."

        # Ensure correct layer
        attr = clip.Attributes
        if attr.LayerIndex != layer_index:
            attr.LayerIndex = layer_index
            doc.Objects.ModifyAttributes(clip.Id, attr, True)

        ClipId = clip.Id
        doc.Views.Redraw()
        return ClipId, "Clipping plane updated to input plane."
    finally:
        sc.doc = prevdoc

# Run
ClipId, Status = main(P, Create, Size)
