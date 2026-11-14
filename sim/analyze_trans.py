"""Stampa la transizione (dall'inizio fino a poco dopo il quad-chute) dall'ultimo .ulg o da quello indicato.
Uso: analyze_trans.py [log.ulg] [passo_s]"""
import sys, glob, os, numpy as np
from pyulog import ULog
logs = sorted(glob.glob(os.path.expanduser("~/PX4-Autopilot/build/px4_sitl_default/rootfs/fs/log/*/*.ulg")), key=os.path.getmtime)
u = ULog(sys.argv[1] if len(sys.argv) > 1 else logs[-1])
step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
vs, att, lp, sv, asp, mo, av = (d[k] for k in ("vehicle_status", "vehicle_attitude", "vehicle_local_position", "actuator_servos", "airspeed_validated", "actuator_motors", "vehicle_angular_velocity"))
T0 = vs["timestamp"][np.argmax(vs["in_transition_mode"] == 1)]
qc = [m.timestamp for m in u.logged_messages if "Quad-chute" in m.message]
end = (qc[0] - T0) / 1e6 + 1 if qc else 40
print(f"quad-chute a {(qc[0] - T0) / 1e6:.2f} s" if qc else "nessun quad-chute")
at = lambda a, T: min(np.searchsorted(a["timestamp"], T), len(a["timestamp"]) - 1)
for dt in np.arange(-0.5, end, step):
    T = T0 + dt * 1e6; q = [att[f"q[{k}]"][at(att, T)] for k in range(4)]
    pitch = np.degrees(np.arcsin(2 * (q[0] * q[2] - q[3] * q[1])))
    roll = np.degrees(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
    p, m, s = at(lp, T), at(mo, T), at(sv, T)
    print(f"{dt:5.1f} roll={roll:6.1f} pitch={pitch:6.1f} q={av['xyz[1]'][at(av, T)]:5.2f} vh={np.hypot(lp['vx'][p], lp['vy'][p]):5.2f} z={lp['z'][p]:6.2f} "
          f"tilt={45 * (sv['control[3]'][s] + 1):4.0f}° el={sv['control[2]'][s]:5.2f} cas={asp['calibrated_airspeed_m_s'][at(asp, T)]:5.1f} "
          f"motF={mo['control[0]'][m]:.2f} motR={mo['control[4]'][m]:.2f} type={vs['vehicle_type'][at(vs, T)]} tr={vs['in_transition_mode'][at(vs, T)]}")
