"""Grafici di volo e stima della potenza elettrica da un log PX4 (.ulg).

Uso: ~/.venvs/cad/bin/python sim/report_plots.py [log.ulg]
Senza argomenti usa il .ulg piu' recente in ~/PX4-Autopilot/build/px4_sitl_default/rootfs/fs/log.
Output in sim/report/<nome_log>/: flight.png, power.png, summary.json
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyulog import ULog

LOGDIR = Path.home() / "PX4-Autopilot/build/px4_sitl_default/rootfs/fs/log"
path = Path(sys.argv[1]) if len(sys.argv) > 1 else max(LOGDIR.glob("*/*.ulg"), key=lambda p: p.stat().st_mtime)
out = Path(__file__).parent / "report" / path.stem
out.mkdir(parents=True, exist_ok=True)

# Modello motore (gen_sdf.py) e parametri del paper (Tab. 10)
K_T, W_MIN, W_SPAN = 1.12e-4, 10.0, 790.0
RHO, A_DISK = 1.225, np.pi * 0.225**2
FOM, ETA = 0.7, 0.92 * 0.95
E_BATT_WH = 1500 * 0.8 * 0.92  # 1.5 kWh, profondita' di scarica 80%, rendimento batteria 0.92

ulog = ULog(str(path))
t0 = ulog.start_timestamp


def topic(name):
    d = ulog.get_dataset(name).data
    return (d["timestamp"] - t0) / 1e6, d


def on(t_src, y, t):
    # porta una serie sulla base dei tempi t (campione precedente piu' vicino)
    return y[np.clip(np.searchsorted(t_src, t, side="right") - 1, 0, len(y) - 1)]


tp, pos = topic("vehicle_local_position")
ta, att = topic("vehicle_attitude")
ts, srv = topic("actuator_servos")
tm, mot = topic("actuator_motors")
tv, st = topic("vehicle_status")
try:
    tas, asp = topic("airspeed_validated")
    cas = asp["calibrated_airspeed_m_s"]
except (KeyError, IndexError, ValueError):
    tas, cas = tp, np.full_like(tp, np.nan)
# alcuni topic chiudono il log con un timestamp spurio: tengo solo l'intervallo della posizione
ok = (tas >= tp[0]) & (tas <= tp[-1]); tas, cas = tas[ok], cas[ok]

# Fasi VTOL: 0 = MC, 1 = transizione, 2 = FW
phase_raw = np.where(st["in_transition_mode"] > 0, 1, np.where(st["vehicle_type"] == 2, 2, 0))
armed = st["arming_state"] == 2
NAMES, COLORS = ["MC", "transizione", "FW"], ["tab:blue", "tab:orange", "tab:green"]

q = [att[f"q[{i}]"] for i in range(4)]
roll = np.degrees(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
pitch = np.degrees(np.arcsin(np.clip(2 * (q[0] * q[2] - q[3] * q[1]), -1, 1)))
tilt = (np.nan_to_num(srv["control[3]"]) + 1) / 2 * 90

# --- flight.png ---
fig, ax = plt.subplots(4, 1, sharex=True, figsize=(10, 10))
ax[0].plot(tp, -pos["z"])
ax[0].set_ylabel("Quota [m]")
ax[1].plot(tp, np.hypot(pos["vx"], pos["vy"]), label="velocita' orizzontale")
ax[1].plot(tas, cas, label="velocita' calibrata (CAS)")
ax[1].set_ylabel("Velocita' [m/s]")
ax[1].legend(loc="upper left")
ax[2].plot(ta, roll, label="rollio")
ax[2].plot(ta, pitch, label="beccheggio")
ax[2].set_ylabel("Assetto [deg]")
ax[2].legend(loc="upper left")
ax[3].plot(ts, tilt)
ax[3].set_ylabel("Tilt ala [deg]")
ax[3].set_xlabel("Tempo [s]")
ax[3].set_xlim(tp[0], tp[-1])
for a in ax:
    a.grid(alpha=0.3)
    # ombreggia solo il tratto armato, fase per fase
    edges = np.append(tv, tp[-1])
    for i, p in enumerate(phase_raw):
        if armed[i]:
            a.axvspan(edges[i], edges[i + 1], color=COLORS[p], alpha=0.12, lw=0)
for p in range(3):
    ax[0].axvspan(0, 0, color=COLORS[p], alpha=0.12, label=NAMES[p])
ax[0].legend(loc="upper left")
fig.suptitle(f"NAIADE - volo {path.stem}")
fig.tight_layout()
fig.savefig(out / "flight.png", dpi=150)

# --- potenza ---
u = np.nan_to_num(np.column_stack([mot[f"control[{i}]"] for i in range(8)]))
w = np.where(u > 0, W_MIN + u * W_SPAN, 0)
T = K_T * w**2  # spinta per motore [N]
P = (T**1.5 / np.sqrt(2 * RHO * A_DISK) / FOM / ETA).sum(axis=1)  # potenza elettrica totale [W]
T_tot = T.sum(axis=1)

ph = on(tv, phase_raw, tm)
arm_m = on(tv, armed.astype(int), tm) == 1
alt_m = on(tp, -pos["z"], tm)
vh_m = on(tp, np.hypot(pos["vx"], pos["vy"]), tm)
vz_m = on(tp, pos["vz"], tm)
# hover stazionario: MC, in quota, quasi fermo
hover = arm_m & (ph == 0) & (alt_m > 2) & (vh_m < 1) & (np.abs(vz_m) < 0.3)

summary = {"log": path.name, "ipotesi": {
    "spinta": "T = 1.12e-4 w^2, w = 10 + 790 u",
    "potenza": "P = T^1.5/sqrt(2 rho A) / FoM / (eta_motore eta_esc), rho 1.225, A pi 0.225^2, FoM 0.7, eta 0.92*0.95",
    "energia_utile_Wh": E_BATT_WH}}
for name, m in [("hover", hover)] + [(NAMES[p], arm_m & (ph == p)) for p in range(3)]:
    if m.sum() < 2:
        continue
    summary[name] = {"durata_s": round(float(m.sum() * np.median(np.diff(tm))), 1),
                     "spinta_tot_media_N": round(float(T_tot[m].mean()), 1),
                     "potenza_media_W": round(float(P[m].mean()), 0)}
    if name == "FW":
        summary[name]["nota"] = "stima da teoria impulsiva (valida solo in hover): indicativa, non e' la potenza di crociera"
if "hover" in summary:
    summary["autonomia_hover_min"] = round(E_BATT_WH / summary["hover"]["potenza_media_W"] * 60, 1)

fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
ax[0].plot(tm, P)
ax[0].set_ylabel("Potenza elettrica stimata [W]")
ax[1].plot(tm, T_tot)
ax[1].set_ylabel("Spinta totale [N]")
ax[1].set_xlabel("Tempo [s]")
for a in ax:
    a.grid(alpha=0.3)
    for p in range(3):
        a.fill_between(tm, 0, 1, where=arm_m & (ph == p), color=COLORS[p], alpha=0.12,
                       transform=a.get_xaxis_transform(), lw=0, label=NAMES[p])
    a.fill_between(tm, 0, 1, where=hover, color="k", alpha=0.08, transform=a.get_xaxis_transform(),
                   lw=0, label="hover stazionario")
ax[0].legend(loc="upper left")
title = f"NAIADE - potenza {path.stem} (teoria impulsiva, valida solo in hover)"
if "hover" in summary:
    title += f"\nhover: {summary['hover']['potenza_media_W']:.0f} W, autonomia {summary['autonomia_hover_min']} min"
fig.suptitle(title)
fig.tight_layout()
fig.savefig(out / "power.png", dpi=150)

(out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(json.dumps(summary, indent=2, ensure_ascii=False))
print(f"Output in {out}")
