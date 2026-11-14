"""Stampa rate/setpoint/motori/servo attorno al decollo dall'ultimo .ulg di PX4 SITL."""
import sys, glob, os, numpy as np
from pyulog import ULog
logs = sorted(glob.glob(os.path.expanduser("~/PX4-Autopilot/build/px4_sitl_default/rootfs/fs/log/*/*.ulg")), key=os.path.getmtime)
u = ULog(sys.argv[1] if len(sys.argv) > 1 else logs[-1])
d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
av, sp, mo, sv, lp = (d[k] for k in ("vehicle_angular_velocity", "vehicle_rates_setpoint", "actuator_motors", "actuator_servos", "vehicle_local_position"))
tt = lp["timestamp"][np.argmax(lp["z"] < -0.3)]
at = lambda arr, T: np.searchsorted(arr["timestamp"], T)
step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
for dt in np.arange(-1, 8, step):
    T = tt + dt * 1e6; a, s, m, v = at(av, T), at(sp, T), at(mo, T), at(sv, T)
    print(f"{dt:5.2f} q={av['xyz[1]'][a]:6.2f} qsp={sp['pitch'][s]:6.2f} p={av['xyz[0]'][a]:6.2f} psp={sp['roll'][s]:6.2f} | mot="
          + " ".join(f"{mo[f'control[{k}]'][m]:.2f}" for k in range(8))
          + f" | tilt={sv['control[3]'][v]:.2f},{sv['control[4]'][v]:.2f}")
