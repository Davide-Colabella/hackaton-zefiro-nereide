"""Deliverable 4 (ID.pdf): schemi funzionali di NEREIDE, in inglese. Un PDF per schema con Graphviz, poi uniti.
Uso: python3 genera_schemi.py  ->  NEREIDE_functional_diagrams.pdf"""
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
NAVY, PANEL, TEAL, ORANGE, YELLOW, WHITE, GREY = "#0d1b24", "#16283a", "#3fb7b0", "#e08a3c", "#e0b400", "#f2f2f2", "#9fb0bd"

HEAD = f'''graph [bgcolor="{NAVY}", fontname="Helvetica", fontcolor="{WHITE}", fontsize=22, labelloc=t, pad=0.5, nodesep=0.35, ranksep=0.55, size="13,7.3!", ratio=fill]
node [shape=box, style="rounded,filled", fillcolor="{PANEL}", color="{TEAL}", fontcolor="{WHITE}", fontname="Helvetica", fontsize=12, penwidth=1.4]
edge [color="{GREY}", fontcolor="{GREY}", fontname="Helvetica", fontsize=10, penwidth=1.3]
'''

def cluster(name, label, color, body):
    return f'subgraph cluster_{name} {{ label="{label}"; fontsize=14; color="{color}"; fontcolor="{color}"; style="rounded,dashed"; {body} }}\n'

SCHEMI = {}

# 1. Architettura elettrica di potenza
SCHEMI["1_elettrica"] = f'''digraph G {{ {HEAD}
label="1 · Electrical power architecture"; rankdir=LR;
batt [label="Battery cartridge\\n1.5 kWh · Li-ion 250 Wh/kg\\n~6 kg, removable", fillcolor="{ORANGE}", fontcolor="{NAVY}"];
bms [label="BMS\\ncell balancing\\nprotection, state of charge"];
conn [label="Head connector\\npower + data"];
pdb [label="Power distribution board\\n(PDB) + current sensor"];
{cluster("prop", "Propulsion · 8 × ~0.95 kW", YELLOW, f'esc [label="8 × ESC\\nη 0.95"]; mot [label="8 × brushless motor\\nη 0.92 · Ø450 propellers"];')}
{cluster("att", "Actuators", TEAL, 'tilt [label="2 × wing tilt servo\\n(front, rear)"]; cs [label="3 × control surface servo\\n2 ailerons + elevator"]; winch [label="Winch motor\\n+ bottle carousel"];')}
bec [label="BEC 5 V / 12 V"];
{cluster("av", "Avionics", GREY, 'fc [label="Flight controller\\nPX4"]; cc [label="Companion computer\\nROS 2"]; sens [label="Sensors and payload\\ncameras, LiDAR, probe"]; radio [label="Telemetry radio\\n+ GNSS"];')}
dock [label="Docking station contacts\\nground power", fillcolor="{TEAL}", fontcolor="{NAVY}"];
batt -> bms -> conn -> pdb;
pdb -> esc [label="HV"]; esc -> mot [label="3 phases"];
pdb -> bec; bec -> tilt; bec -> cs; bec -> winch; bec -> fc; bec -> cc; bec -> sens; bec -> radio;
dock -> conn [style=dashed, label="on the ground"];
}}'''

# 2. Flusso dei dati e avionica
SCHEMI["2_dati"] = f'''digraph G {{ {HEAD}
label="2 · Data flow: sensors → decision → users"; rankdir=LR;
{cluster("nav", "Flight sensors", TEAL, 'imu [label="IMU + magnetometer"]; gnss [label="GNSS"]; baro [label="Barometer"]; pitot [label="Pitot tube\\n(airspeed)"]; lidar [label="LiDAR altimeter\\n(height over water)"];')}
{cluster("pay", "Mission sensors", YELLOW, 'cam [label="Thermal + RGB camera\\n(gimbal)"]; ms [label="Multispectral camera\\n5 bands"]; aria [label="Air quality\\n+ weather station"]; sonda [label="Multi-parameter probe\\npH, T, conductivity, O₂, turbidity"];')}
fc [label="PX4 flight controller\\nstate estimation (EKF2)\\ncontrol and mission", fillcolor="{TEAL}", fontcolor="{NAVY}"];
cc [label="ROS 2 companion computer\\ndata fusion, decision\\nanalyse or sample"];
store [label="On-board storage\\nbottle: code, GPS, time, T"];
radio [label="Telemetry radio"];
gcs [label="Ground operator\\nsupervision"];
base [label="Docking station\\ndata download via contacts"];
utenti [label="Environmental agencies · water utilities\\nCivil Protection", fillcolor="{ORANGE}", fontcolor="{NAVY}"];
imu -> fc; gnss -> fc; baro -> fc; pitot -> fc; lidar -> fc;
cam -> cc; ms -> cc; aria -> cc; sonda -> cc;
fc -> cc [label="uXRCE-DDS", dir=both];
cc -> store; cc -> radio [label="real-time data"]; fc -> radio [label="MAVLink", dir=both];
radio -> gcs [dir=both]; store -> base [label="on return"];
gcs -> utenti; base -> utenti [label="validated data\\nfor the laboratories"];
}}'''

# 3. Catena di controllo del volo (come in simulazione)
SCHEMI["3_controllo"] = f'''digraph G {{ {HEAD}
label="3 · Flight control chain (PX4, verified in simulation)"; rankdir=LR;
mis [label="Mission\\nwaypoints, hover, landing"];
pos [label="Position control\\nhover: MPC · cruise: TECS + NPFG"];
vtol [label="Tilt-wing VTOL logic\\nphases and wing rotation", fillcolor="{YELLOW}", fontcolor="{NAVY}"];
att [label="Attitude control"];
rate [label="Angular rate control\\n(gains ×3 vs a quadcopter:\\ninertia of a 3 m span)"];
ca [label="Control allocation\\neffectiveness matrix", fillcolor="{TEAL}", fontcolor="{NAVY}"];
mot [label="8 motors\\nthrust + yaw torque"];
tilt [label="2 tilt servos\\n0° hover · 90° cruise"];
cs [label="Ailerons + elevator\\n(cruise only)"];
ekf [label="EKF2 state estimation\\nIMU, GNSS, baro, Pitot"];
mis -> pos -> att -> rate -> ca;
vtol -> att [label="hover/cruise weights"]; vtol -> tilt [label="wing angle"];
ca -> mot; ca -> cs;
ekf -> pos [style=dashed]; ekf -> att [style=dashed]; ekf -> vtol [label="airspeed", style=dashed];
}}'''

# 4. Architettura meccanica e moduli
SCHEMI["4_meccanica"] = f'''digraph G {{ {HEAD}
label="4 · Mechanical architecture: fixed structure, moving parts, modules"; rankdir=TB;
fus [label="Fuselage\\ncomposite / foam", fillcolor="{YELLOW}", fontcolor="{NAVY}"];
{cluster("wing", "Tilting box wing", YELLOW, 'wa [label="Front wing\\nNACA 2415 · chord 280"]; wp [label="Rear wing\\nNACA 2415 · chord 280"]; pa [label="Pivot + servo\\nfront wing"]; pp [label="Pivot + servo\\nrear wing"]; ale [label="Wingtip plates\\nclose the box"]; nac [label="8 motor nacelles\\nrotate with the wing"];')}
der [label="Fin\\nsupports the rear wing"];
{cluster("ven", "Belly fairing · swappable modules", TEAL, 'ver [label="Winch\\n12 m Dyneema line"]; car [label="Carousel\\n4 × 250 ml bottles"]; son [label="Probe\\nØ48 × 174 mm"]; bat [label="Battery cartridge\\nrails + snap latch"];')}
pat [label="Skids with cross-bar\\nresting + docking to the base"];
fus -> pa -> wa; fus -> der -> pp -> wp; wa -> ale [dir=none]; wp -> ale [dir=none]; wa -> nac [dir=none]; wp -> nac [dir=none];
fus -> ver -> son; fus -> car; fus -> bat; fus -> pat;
}}'''

# 5. Missione tipo (stati)
SCHEMI["5_missione"] = f'''digraph G {{ {HEAD}
label="5 · Typical mission (simulated: 260 s, base → lake 1 km → base)"; rankdir=LR;
node [shape=box];
a [label="Solar base\\ncharged battery\\nclean bottles", fillcolor="{TEAL}", fontcolor="{NAVY}"];
b [label="Vertical take-off\\nwings at 90°"];
c [label="Transition\\nwings rotate in 10 s"];
d [label="Cruise\\nstraight line · 40 m"];
e [label="Braking\\nback to hover"];
f [label="Hover at 10 m\\nover the water", fillcolor="{YELLOW}", fontcolor="{NAVY}"];
g [label="Battery high:\\non-site analysis ~3 min"];
h [label="Otherwise:\\nbottle sample in 90 s"];
i [label="Return\\ntransition + cruise"];
l [label="Guided landing\\nnose aligned, < 10 cm"];
m [label="Samples unloaded\\nbattery swap < 2 min", fillcolor="{ORANGE}", fontcolor="{NAVY}"];
a -> b -> c -> d -> e -> f; f -> g [label="decides\\nmission + battery"]; f -> h; g -> i; h -> i; i -> l -> m; m -> a [style=dashed, label="next mission"];
}}'''

# 6. Docking station e cambio batteria
SCHEMI["6_docking"] = f'''digraph G {{ {HEAD}
label="6 · Docking station: sample unloading and battery swap"; rankdir=LR;
{cluster("st", "Solar base on the treatment plant", TEAL, 'sol [label="A · Solar panel ~4 m²"]; acc [label="F · Technical room\\nstorage battery"]; mag [label="D · Magazine\\n3 rotating batteries", fillcolor="#e08a3c", fontcolor="#0d1b24"]; ele [label="E · Battery lift"]; fri [label="C · Sample fridge 4 °C"]; gui [label="B · Cone guides\\n+ contacts"];')}
s1 [label="1 · Guided landing\\noptical marker + cones"];
s2 [label="2 · Connection\\ncontacts: power + data"];
s3 [label="3 · Samples\\ncarousel lowered into the fridge"];
s4 [label="4 · Battery swap\\nlatch opens, the lift pulls out\\nthe empty one, inserts a charged one"];
s5 [label="5 · Take-off again\\n< 2 minutes"];
s1 -> s2 -> s3 -> s4 -> s5;
sol -> acc -> mag [label="slow charging"]; mag -> ele -> s4 [style=dashed]; fri -> s3 [style=dashed]; gui -> s1 [style=dashed]; gui -> s2 [style=dashed];
}}'''

pdfs = []
for name, dot in SCHEMI.items():
    out = HERE / f"{name}.pdf"
    subprocess.run(["dot", "-Tpdf", "-o", str(out)], input=dot, text=True, check=True)
    subprocess.run(["dot", "-Tpng", "-Gdpi=110", "-o", str(HERE / f"{name}.png")], input=dot, text=True, check=True)
    pdfs.append(str(out))
subprocess.run(["pdfunite", *pdfs, str(HERE / "NEREIDE_functional_diagrams.pdf")], check=True)
print("ok:", HERE / "NEREIDE_functional_diagrams.pdf", f"({len(pdfs)} schemi)")
