"""STEP -> mesh STL per Gazebo, gruppi separati per colore (corpo, ali, gondole, eliche prop_0..7).
Frame modello (FLU): x = cad_y, y = -cad_x, z = cad_z, metri. Ali riferite al proprio perno.
Uso: python export_meshes.py NAIADE.step cartella_output"""
import sys
from pathlib import Path
import numpy as np, trimesh
from OCP.STEPControl import STEPControl_Reader
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

STEP = Path(sys.argv[1]); OUT = Path(sys.argv[2])
# indici solidi 1-based nell'ordine dello STEP
GROUPS = {
    "front_wing": [2], "front_nacelles": [7, 8, 9, 10],
    "rear_wing": [3], "rear_nacelles": [11, 12, 13, 14],
    "endplates": [4, 5], "fairing": [15], "battery": [16], "skids": [39],
    "sensors": [30, 31, 32, 33, 34, 35, 37, 38],
    # parti mobili della missione: sonda sul verricello, carosello flaconi
    "probe": [23], "carousel": [24, 25, 26, 27, 28, 29],
}
SKIP = {22}  # cavo: in simulazione è fatto a segmenti telescopici
PIVOT = {"front": np.array([0.26, 0, -0.065]), "rear": np.array([-0.45, 0, 0.29])}

r = STEPControl_Reader()
assert r.ReadFile(str(STEP)) == 1, "lettura STEP fallita"
r.TransferRoots(); shape = r.OneShape()
BRepMesh_IncrementalMesh(shape, 0.8, False, 0.3, True)  # deflessione 0.8 mm

solids, ex = [], TopExp_Explorer(shape, TopAbs_SOLID)
while ex.More():
    solids.append(TopoDS.Solid(ex.Current())); ex.Next()
assert len(solids) == 39, f"lo STEP è cambiato ({len(solids)} solidi): aggiorna GROUPS"

# controllo che l'ordine corrisponda: il solido 2 è l'ala anteriore (Y 120..400 mm)
b = Bnd_Box(); BRepBndLib.Add_s(solids[1], b); ymin = b.CornerMin().Y()
assert 100 < ymin < 140, f"ordine solidi inatteso (ymin={ymin})"

def solid_mesh(solid):
    verts, faces, ex = [], [], TopExp_Explorer(solid, TopAbs_FACE)
    while ex.More():
        face = TopoDS.Face(ex.Current()); loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf, off = loc.Transformation(), sum(len(v) for v in verts)
            v = [tri.Node(i).Transformed(trsf) for i in range(1, tri.NbNodes() + 1)]
            verts.append(np.array([[p.X(), p.Y(), p.Z()] for p in v]))
            f = np.array([tri.Triangle(i).Get() for i in range(1, tri.NbTriangles() + 1)]) - 1 + off
            faces.append(f[:, ::-1] if face.Orientation() == TopAbs_REVERSED else f)
        ex.Next()
    return trimesh.Trimesh(np.vstack(verts), np.vstack(faces))

def to_model(m):
    v = m.vertices / 1000.0
    m.vertices = np.c_[v[:, 1], -v[:, 0], v[:, 2]]
    return m

def split_prop(m):
    # elica fusa nella gondola (asse // Y CAD): le pale sporgono oltre il raggio gondola (40 mm)
    c = m.bounds.mean(axis=0)
    r = np.hypot(m.vertices[:, 0] - c[0], m.vertices[:, 2] - c[2])
    yb = m.vertices[r > 50, 1]
    # fine del cilindro gondola 19 mm prima delle pale: da lì in avanti ogiva + pale ruotano
    prop = m.vertices[m.faces, 1].min(axis=1) > yb.min() - 20
    hub = np.array([c[0], (yb.min() + yb.max()) / 2, c[2]])
    return m.submesh([~prop], append=True), m.submesh([prop], append=True), hub

used = {i for g in GROUPS.values() for i in g} | SKIP
GROUPS["body"] = [i for i in range(1, 40) if i not in used]
for name, ids in GROUPS.items():
    side = name.split("_")[0]
    meshes = [solid_mesh(solids[i - 1]) for i in ids]
    if name.endswith("_nacelles"):
        assert all(np.diff([mm.bounds[0, 0] for mm in meshes]) > 0), "gondole non ordinate per X CAD"
        base = 0 if side == "front" else 4   # motori 0-3 ala anteriore, ordine y +1.0 .. -1.0 = X CAD crescente
        for k, mm in enumerate(meshes):
            meshes[k], prop, hub = split_prop(mm)
            prop = to_model(prop); hub = to_model(trimesh.Trimesh([hub], [])).vertices[0]
            prop.vertices -= hub  # centrata sul mozzo, ancora in assetto crociera
            prop.export(OUT / f"prop_{base + k}.stl")
            d = hub - PIVOT[side]
            print(f"prop_{base + k}", len(prop.faces), "tri, mozzo da perno [m]", d.round(4).tolist())
    m = to_model(trimesh.util.concatenate(meshes))
    if side in PIVOT:
        m.vertices -= PIVOT[side]
    m.export(OUT / f"{name}.stl")
    print(name, len(m.faces), "tri", m.bounds.round(3).tolist())
