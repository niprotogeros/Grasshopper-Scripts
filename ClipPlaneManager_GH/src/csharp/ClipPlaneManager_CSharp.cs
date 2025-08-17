// Clipping Plane Manager (C# for Grasshopper Script component)
using System;
using System.Linq;
using System.Collections.Generic;
using Rhino;
using Rhino.Geometry;
using Rhino.DocObjects;

private int EnsureLayer(RhinoDoc doc, string name)
{
  int index = doc.Layers.Find(name, true);
  if (index < 0)
  {
    var layer = new Layer { Name = name, IsVisible = true, IsLocked = false };
    index = doc.Layers.Add(layer);
  }
  else
  {
    var layer = doc.Layers[index];
    if (layer.IsDeleted) { layer.IsDeleted = false; doc.Layers.Modify(layer, index, true); }
    if (layer.IsLocked)  { layer.IsLocked  = false; doc.Layers.Modify(layer, index, true); }
  }
  return index;
}

private List<Guid> AllViewportIds(RhinoDoc doc)
{
  var views = doc.Views.GetViewList(true, true);
  var ids = new List<Guid>();
  foreach (var v in views)
  {
    try { ids.Add(v.ActiveViewportID); } catch { }
  }
  if (ids.Count == 0 && doc.Views.ActiveView != null)
    ids.Add(doc.Views.ActiveView.ActiveViewportID);
  return ids.Distinct().ToList();
}

private Guid CreateClip(RhinoDoc doc, Plane plane, double size, int layerIndex, IEnumerable<Guid> vps)
{
  if (size <= 0.0) size = 1000.0;
  Guid id = doc.Objects.AddClippingPlane(plane, size, size, vps);
  if (id == Guid.Empty) return Guid.Empty;

  var attr = new ObjectAttributes { LayerIndex = layerIndex };
  doc.Objects.ModifyAttributes(id, attr, true);
  return id;
}

private Rhino.DocObjects.ClippingPlaneObject[] GetClipsInLayer(RhinoDoc doc, string layerName)
{
  var ros = doc.Objects.FindByLayer(layerName);
  if (ros == null || ros.Length == 0) return new Rhino.DocObjects.ClippingPlaneObject[0];
  return ros.OfType<Rhino.DocObjects.ClippingPlaneObject>().ToArray();
}

// Inputs: P (Plane), Create (bool), Size (double)
// Outputs: ClipId (Guid), Status (string)
private void RunScript(Plane P, bool Create, double Size, ref object ClipId, ref object Status)
{
  var doc = RhinoDoc.ActiveDoc;
  if (doc == null) { Status = "No active Rhino document."; return; }

  int layerIndex = EnsureLayer(doc, "Clipping Plane");
  var viewIds = AllViewportIds(doc);

  var clips = GetClipsInLayer(doc, "Clipping Plane").ToList();

  if (clips.Count == 0 && Create)
  {
    Guid nid = CreateClip(doc, Plane.WorldXY, Size, layerIndex, viewIds);
    if (nid == Guid.Empty) { Status = "Failed to create clipping plane."; return; }
    clips = GetClipsInLayer(doc, "Clipping Plane").ToList();
  }

  if (clips.Count > 1)
  {
    clips = clips.OrderBy(c => c.Id).ToList();
    for (int i = 1; i < clips.Count; i++)
      doc.Objects.Delete(clips[i], true);
    clips = new List<Rhino.DocObjects.ClippingPlaneObject> { clips[0] };
  }

  if (clips.Count == 0)
  {
    Status = "No clipping plane in layer 'Clipping Plane'. Set Create=true to make one on World XY.";
    ClipId = Guid.Empty;
    return;
  }

  var clip = clips[0];
  var cgeom = clip.ClippingPlaneGeometry;
  Plane current;
  if (!cgeom.TryGetPlane(out current))
    current = cgeom.Plane;

  var xform = Transform.PlaneToPlane(current, P);
  bool ok = doc.Objects.Transform(clip.Id, xform, true);

  if (!ok)
  {
    doc.Objects.Delete(clip, true);
    Guid nid = CreateClip(doc, P, Size, layerIndex, viewIds);
    if (nid == Guid.Empty) { Status = "Failed to reposition; could not recreate."; ClipId = Guid.Empty; return; }
    ClipId = nid;
    Status = "Recreated clipping plane at input plane.";
    doc.Views.Redraw();
    return;
  }

  var attr = clip.Attributes;
  if (attr.LayerIndex != layerIndex)
  {
    attr.LayerIndex = layerIndex;
    doc.Objects.ModifyAttributes(clip.Id, attr, true);
  }

  ClipId = clip.Id;
  Status = "Clipping plane updated to input plane.";
  doc.Views.Redraw();
}
