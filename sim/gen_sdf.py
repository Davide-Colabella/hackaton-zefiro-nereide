"""Genera sim/naiade/model.sdf: tandem box-wing tilt-wing, 8 motori, 2 ali basculanti.
Frame FLU (x avanti, y sinistra, z su), metri. Giunto ala = 0 -> hover (nacelle verso l'alto), +90° -> crociera.
Valori di massa/inerzia/motori sono STIME da sostituire con i dati di progetto."""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "naiade"
TILTROTOR = Path.home() / "PX4-Autopilot/Tools/simulation/gz/models/tiltrotor/model.sdf"

MASS = 21.8                      # MTOW 25 kg (slide 4) meno ali (2 x 1.5 kg) e rotori
CG = (0.06, 0.0, -0.05)         # avanti rispetto al punto medio tra le ali: margine statico in crociera
INERTIA = (4.6, 2.8, 7.4)        # ixx iyy izz senza ali, scalati da 18 a 25 kg [kg m^2]
PIVOT = {"front": (0.26, 0, -0.065), "rear": (-0.45, 0, 0.29)}
PROP_ARM = {"front": 0.38, "rear": 0.37}    # distanza perno -> disco elica lungo la gondola
PROP_HUB = {"front": 0.355, "rear": 0.345}  # mozzo misurato sul CAD: sposta solo la mesh, non la spinta
SPAN_Y = (1.0, 0.4, -0.4, -1.0)
# verso di rotazione: coppie speculari opposte, ala anteriore e posteriore invertite
DIRS = {"front": ("ccw", "cw", "ccw", "cw"), "rear": ("cw", "ccw", "cw", "ccw")}
MOTOR_K, MAX_W, MOMENT_K = 1.12e-4, 800, 0.05   # T = k w^2 -> ~72 N/motore: T/W 2.3 a 25 kg, margine per la transizione
HALF_AREA = 1.5 * 0.28           # semiala: apertura 1.5 m x corda 0.28 m

def inertial(m, i):
    return f"<inertial><mass>{m}</mass><inertia><ixx>{i[0]}</ixx><ixy>0</ixy><ixz>0</ixz><iyy>{i[1]}</iyy><iyz>0</iyz><izz>{i[2]}</izz></inertia></inertial>"

def mesh_visual(name, color, pose="0 0 0 0 0 0"):
    # ogre2 ignora i colori se manca specular: lo teniamo basso per non sbiadire
    return (f"<visual name='{name}'><pose>{pose}</pose><geometry><mesh><uri>model://naiade/meshes/{name}.stl</uri></mesh></geometry>"
            f"<material><ambient>{color}</ambient><diffuse>{color}</diffuse><specular>0.2 0.2 0.2 1</specular></material></visual>")

def lift_drag(link, cp, forward, upward, area, control=None, k=-1.0, a0=0.035):
    ctrl = f"<control_joint_name>{control}</control_joint_name><control_joint_rad_to_cl>{k}</control_joint_rad_to_cl>" if control else ""
    # stallo: portanza che cala verso 0 a 90°, resistenza che cresce (comportamento da lastra piana durante la transizione)
    return f"""<plugin filename="gz-sim-lift-drag-system" name="gz::sim::systems::LiftDrag">
      <a0>{a0}</a0><cla>4.75</cla><cda>0.6</cda><cma>0</cma>
      <alpha_stall>0.25</alpha_stall><cla_stall>-0.9</cla_stall><cda_stall>0.6</cda_stall><cma_stall>0</cma_stall>
      <cp>{cp}</cp><area>{area}</area><air_density>1.2041</air_density>
      <forward>{forward}</forward><upward>{upward}</upward><link_name>{link}</link_name>{ctrl}</plugin>"""

def pos_ctrl(joint, topic, p=100):
    return f"""<plugin filename="gz-sim-joint-position-controller-system" name="gz::sim::systems::JointPositionController">
      <joint_name>{joint}</joint_name><sub_topic>{topic}</sub_topic><p_gain>{p}</p_gain><i_gain>0</i_gain><d_gain>{p / 20}</d_gain>
      <cmd_max>{p}</cmd_max><cmd_min>-{p}</cmd_min></plugin>"""

def dummy_surface(name, parent, axis="0 1 0", lim=0.5):
    return f"""<link name='{name}'><pose relative_to='{parent}'>0 0 0 0 0 0</pose>{inertial(1e-3, (2e-3,)*3)}</link>
    <joint name='{name}_joint' type='revolute'><parent>{parent}</parent><child>{name}</child>
      <axis><xyz>{axis}</xyz><limit><lower>-{lim}</lower><upper>{lim}</upper></limit><dynamics><damping>0.2</damping></dynamics></axis></joint>"""

base = TILTROTOR.read_text()
sensors = "\n".join(re.findall(r"<sensor .*?</sensor>", base, re.S))
airspeed = re.search(r"<include merge=\"true\">\s*<uri>model://airspeed</uri>.*?</joint>", base, re.S).group(0)

parts, plugins, motor_no = [], [], 0
white, slate, teal = "0.9 0.9 0.9 1", "0.08 0.08 0.08 1", "0.85 0.68 0.0 1"
yellow, ink = "0.85 0.68 0.0 1", "0.08 0.08 0.08 1"  # livrea NEREIDE (CAD 14/11): ali e carenatura gialle, resto nero
black, grey, orange = "0.06 0.07 0.08 1", "0.6 0.62 0.65 1", "0.75 0.4 0.1 1"

for i, side in enumerate(("front", "rear")):
    px, py, pz = PIVOT[side]
    wing = f"{side}_wing"
    # mesh in assetto crociera -> ruotata di -90° in pitch per avere l'hover a giunto 0
    parts.append(f"""<link name='{wing}'><pose>{px} {py} {pz} 0 0 0</pose>{inertial(1.5, (1.1, 0.18, 1.2))}
      <collision name='{wing}_coll'><geometry><box><size>0.04 3.0 0.28</size></box></geometry></collision>
      {mesh_visual(wing, yellow, "0 0 0 0 -1.5708 0")}{mesh_visual(f"{side}_nacelles", slate, "0 0 0 0 -1.5708 0")}</link>
    <joint name='{wing}_joint' type='revolute'><parent>base_link</parent><child>{wing}</child>
      <axis><xyz>0 1 0</xyz><limit><lower>0</lower><upper>1.5708</upper></limit><dynamics><damping>2</damping></dynamics></axis></joint>""")
    plugins.append(pos_ctrl(f"{wing}_joint", f"servo_{3 + i}", p=200))
    # portanza sull'ala basculante: in frame link, la corda (avanti in crociera) è +z, il dorso è -x
    for s, sy in (("left", 0.75), ("right", -0.75)):
        surf = "aileron_left" if side == "front" and s == "left" else "aileron_right" if side == "front" else "elevator"
        plugins.append(lift_drag(wing, f"0 {sy} 0.07", "0 0 1", "-1 0 0", HALF_AREA, surf + "_joint", -0.6 if surf == "elevator" else -1.0))
    for j, (y, d) in enumerate(zip(SPAN_Y, DIRS[side])):
        rotor = f"rotor_{motor_no}"
        parts.append(f"""<link name='{rotor}'><pose relative_to='{wing}'>0 {y} {PROP_ARM[side]} 0 0 0</pose>{inertial(0.03, (2.5e-4, 2.5e-4, 5e-4))}
      {mesh_visual(f"prop_{motor_no}", black, f"0 0 {PROP_HUB[side] - PROP_ARM[side]:.3f} 0 -1.5708 0")}</link>
    <joint name='{rotor}_joint' type='revolute'><parent>{wing}</parent><child>{rotor}</child>
      <axis><xyz>0 0 1</xyz><limit><lower>-1e16</lower><upper>1e16</upper></limit></axis></joint>""")
        plugins.append(f"""<plugin filename="gz-sim-multicopter-motor-model-system" name="gz::sim::systems::MulticopterMotorModel">
      <jointName>{rotor}_joint</jointName><linkName>{rotor}</linkName><turningDirection>{d}</turningDirection>
      <timeConstantUp>0.03</timeConstantUp><timeConstantDown>0.05</timeConstantDown><maxRotVelocity>{MAX_W}</maxRotVelocity>
      <motorConstant>{MOTOR_K}</motorConstant><momentConstant>{MOMENT_K}</momentConstant>
      <commandSubTopic>command/motor_speed</commandSubTopic><motorNumber>{motor_no}</motorNumber>
      <rotorDragCoefficient>8.06e-05</rotorDragCoefficient><rollingMomentCoefficient>1e-06</rollingMomentCoefficient>
      <rotorVelocitySlowdownSim>10</rotorVelocitySlowdownSim><motorType>velocity</motorType></plugin>""")
        motor_no += 1

# superfici di controllo fittizie: muovono il cl delle semiali tramite LiftDrag
for surf, parent, topic in (("aileron_left", "front_wing", 0), ("aileron_right", "front_wing", 1), ("elevator", "rear_wing", 2)):
    parts.append(dummy_surface(surf, parent))
    plugins.append(pos_ctrl(f"{surf}_joint", f"servo_{topic}", p=10))
# parti mobili della missione: solo grafica (massa trascurabile, senza gravità), la massa vera resta in base_link
WINCH = (-0.27, 0, -0.18)        # uscita del cavo sotto il verricello
N_SEG, L_SEG = 34, 0.3           # cavo telescopico: 34 x 0.3 m = 10.2 m; retratto resta dentro la fusoliera

def mover(name, parent, pose, lower, upper, visual, topic):
    parts.append(f"""<link name='{name}'><pose relative_to='{parent}'>{pose}</pose>{inertial(1e-2, (1e-4,)*3)}<gravity>0</gravity>{visual}</link>
    <joint name='{name}_joint' type='prismatic'><parent>{parent}</parent><child>{name}</child>
      <axis><xyz>0 0 1</xyz><limit><lower>{lower}</lower><upper>{upper}</upper></limit><dynamics><damping>0.6</damping></dynamics></axis></joint>""")
    # 10 g, p 10, smorzamento ~critico: abbastanza rigido da non scivolare in accelerazione, stabile col passo di 4 ms
    plugins.append(f"""<plugin filename="gz-sim-joint-position-controller-system" name="gz::sim::systems::JointPositionController">
      <joint_name>{name}_joint</joint_name><sub_topic>{topic}</sub_topic><p_gain>10</p_gain><i_gain>0</i_gain><d_gain>0</d_gain>
      <cmd_max>10</cmd_max><cmd_min>-10</cmd_min></plugin>""")

cable = (f"<visual name='cable'><pose>0 0 {L_SEG / 2} 0 0 0</pose><geometry><cylinder><radius>0.002</radius><length>{L_SEG}</length></cylinder></geometry>"
         f"<material><ambient>{black}</ambient><diffuse>{black}</diffuse><specular>0.2 0.2 0.2 1</specular></material></visual>")
prev = "base_link"
# NO_CABLE=1: senza cavo la simulazione va ~2.5x più veloce (34 link in meno), per i test rapidi
import os
for k in range(0 if os.environ.get("NO_CABLE") else N_SEG):
    # ogni segmento scende di (lunghezza cavo)/N rispetto al precedente: comando su winch_cable = -lunghezza/N
    mover(f"cable_{k}", prev, " ".join(map(str, WINCH)) + " 0 0 0" if k == 0 else "0 0 0 0 0 0", -L_SEG, 0, cable, "winch_cable")
    prev = f"cable_{k}"
# sonda: la mesh CAD è calata di 0.36 m, la alzo così che posizione 0 = ritratta; comando su winch = -discesa [m]
mover("probe", "base_link", "0 0 0.36 0 0 0", -10.2, 0, mesh_visual("probe", "0.9 0.9 0.9 1"), "winch")
mover("carousel", "base_link", "0 0 0 0 0 0", -0.6, 0, mesh_visual("carousel", "0.3 0.6 0.85 1"), "carousel")
mover("battery", "base_link", "0 0 0 0 0 0", -0.6, 0, mesh_visual("battery", orange), "battery")

# deriva fissa (stabilità di imbardata)
plugins.append(lift_drag("base_link", "-0.55 0 0.15", "1 0 0", "0 1 0", 0.08, a0=0))

skids = "".join(f"""<collision name='skid_{n}'><pose>-0.04 {y} -0.28 0 0 0</pose><geometry><box><size>0.68 0.024 0.024</size></box></geometry></collision>"""
                for n, y in (("l", 0.21), ("r", -0.21)))

sdf = f"""<?xml version="1.0"?>
<!-- Generato da sim/gen_sdf.py: non modificare a mano -->
<sdf version="1.9">
  <model name="naiade">
    <pose>0 0 0.30 0 0 0</pose>
    <link name="base_link">
      <inertial><pose>{" ".join(map(str, CG))} 0 0 0</pose><mass>{MASS}</mass>
        <inertia><ixx>{INERTIA[0]}</ixx><ixy>0</ixy><ixz>0</ixz><iyy>{INERTIA[1]}</iyy><iyz>0</iyz><izz>{INERTIA[2]}</izz></inertia></inertial>
      {skids}
      <collision name='fuselage'><pose>0.07 0 0 0 1.5708 0</pose><geometry><cylinder><radius>0.11</radius><length>1.6</length></cylinder></geometry></collision>
      {mesh_visual("body", ink)}
      {mesh_visual("endplates", ink)}
      {mesh_visual("fairing", yellow)}
      {mesh_visual("skids", grey)}
      {mesh_visual("sensors", black)}
      {sensors}
    </link>
    {airspeed}
    {"".join(parts)}
    {"".join(plugins)}
  </model>
</sdf>
"""
(OUT / "model.sdf").write_text(sdf)
(OUT / "model.config").write_text("""<?xml version="1.0"?>
<model><name>naiade</name><version>0.1</version><sdf version="1.9">model.sdf</sdf>
<description>NEREIDE eVTOL tandem tilt-wing (simulazione di missione)</description></model>
""")
print("ok", motor_no, "motori")
