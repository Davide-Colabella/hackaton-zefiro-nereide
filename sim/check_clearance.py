"""Distanza minima del volo dagli ostacoli del mondo NEREIDE e dal suolo, per fase (MC / transizione / FW).
Uso: check_clearance.py [log.ulg]  (default: ultimo log in sim/logs)"""
import glob, os, re, sys
import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
log = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(f"{HERE}/logs/*.ulg"), key=os.path.getmtime)
world = open(f"{HERE}/worlds/nereide.sdf").read()

# ostacoli come scatole allineate agli assi (x est, y nord, quota max), dalle collisioni del mondo
obst = []
for name, body in re.findall(r"<model name=['\"]([^'\"]+)['\"]>(.*?)</model>", world, re.S):
    if "<collision" not in body or name == "ground_plane":
        continue
    px, py = map(float, re.search(r"<pose>([^<]+)</pose>", body).group(1).split()[:2])
    top, half = 0.0, 0.0
    for c in re.findall(r"<collision.*?</collision>", body, re.S):
        z = float(re.search(r"<pose>([^<]+)</pose>", c).group(1).split()[2]) if "<pose>" in c else 0.0
        if m := re.search(r"<size>([^<]+)</size>", c):
            sx, sy, sz = map(float, m.group(1).split()); top = max(top, z + sz / 2); half = max(half, sx / 2, sy / 2)
        elif m := re.search(r"<radius>([^<]+)</radius>", c):
            r = float(m.group(1)); L = re.search(r"<length>([^<]+)</length>", c)
            top = max(top, z + (float(L.group(1)) / 2 if L else r)); half = max(half, r)
    obst.append((name, px, py, half, top))

u = ULog(log)
lp, vs = u.get_dataset("vehicle_local_position").data, u.get_dataset("vehicle_status").data
E, N, H = lp["y"], lp["x"], -lp["z"]  # PX4 NED -> mondo ENU
phase = np.where(vs["in_transition_mode"] > 0, "transizione", np.where(vs["vehicle_type"] == 2, "FW", "MC"))
ph = phase[np.clip(np.searchsorted(vs["timestamp"], lp["timestamp"]) - 1, 0, len(phase) - 1)]
far = np.hypot(E, N) > 5  # lontano dalla base: l'atterraggio non conta come quota bassa
for p in ("MC", "transizione", "FW"):
    m = (ph == p) & far
    if m.any():
        print(f"{p:12s} quota minima lontano dalla base: {H[m].min():5.1f} m")
worst = []
for name, ox, oy, half, top in obst:
    d_h = np.maximum(np.hypot(E - ox, N - oy) - half, 0)    # distanza orizzontale dal bordo
    above = H - top                                          # margine verticale sopra la cima
    clear = np.where(above > 0, np.hypot(d_h, above), d_h)  # sotto la cima conta solo la distanza laterale
    i = np.argmin(clear); worst.append((clear[i], name, d_h[i], above[i]))
for c, name, dh, ab in sorted(worst)[:5]:
    print(f"{name:16s} distanza minima {c:6.1f} m (orizzontale {dh:5.1f}, sopra la cima {ab:5.1f})")
assert sorted(worst)[0][0] > 2.0, "il volo passa a meno di 2 m da un ostacolo"
print("ok: nessun ostacolo entro 2 m")
