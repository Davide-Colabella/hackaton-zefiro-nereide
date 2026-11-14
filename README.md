# NEREIDE — Team 26 · IBEC Innovative Design (powered by ZEFIRO)

NEREIDE is a **tilt-wing box-wing eVTOL** that patrols urban rivers, lakes and coasts. It flies like an aeroplane, hovers about 10 m above the water, and either **analyses** the water on the spot with a winch-lowered probe or **takes a sample**. It then returns to a **solar base** that puts the samples in a 4 °C fridge and **swaps the battery in under 2 minutes**.

Only the architecture comes from the TiltOne (Palaia et al., *Applied Sciences* 11, 2021): box wing, tilting wings, 8 propellers. Mission, modules, winch, base, sizing, CAD and simulation are the team's own work.

Repository: CAD · simulation · delivered documents. Everything is in English except the simulation notes and scripts' comments, which are in Italian.

## Key numbers

| | |
|---|---|
| Span / length | 3.06 m / 1.74 m |
| Wings | 2 × 3.0 × 0.28 m, NACA 2415, staggered 710 mm, joined by wingtip plates |
| Take-off mass | 25 kg (weight 245 N) |
| Propulsion | 8 propellers Ø 450 mm, thrust/weight 2.3 |
| Battery | 1.5 kWh removable cartridge, 20% safety reserve |
| Design cruise | 108 km/h (30 m/s); the simulated demo is flown at 75 km/h |
| Hover / cruise power | 3.4 kW / 0.66 kW (team sizing) |

## What was delivered (`CONSEGNA_TEAM_26/`)

Following the ID.pdf deliverables:

| File | Content |
|---|---|
| `26.pdf` | The concise document, 10 slides (the PDF named `TEAM_NUMBER.pdf`) |
| `26.pptx` | Same slides with speaker notes and the simulation video embedded in slide 10 |
| `26_video_prototype.mp4` | 1:5 scale model video (3:32, English captions). *Not in this repository: 114 MB, above GitHub's file limit* |
| `26_sketches_graphic_tables.pdf` | Optional: 5 drawing sheets (views, bill of materials, details) |
| `26_functional_diagrams.pdf` | Optional: 6 functional diagrams (electrical power, data flow, flight control, mechanics, mission, docking station) |
| `26_video_simulation.mp4` | Extra: the full mission in simulation, 55 s |
| `26_CAD_NEREIDE.step`, `26_CAD_NEREIDE_with_base.step` | Extra: full-scale 3D CAD (aircraft, and aircraft docked on the base) |

The slides cover: mission and objectives, what is new, the concept, propulsion and flight principles, structure and modules, analysis-or-sampling logic, energy and motor consumption, the docking station with battery swap (bonus), and the scale model with the simulation.

## Repository layout

| Path | Content |
|---|---|
| `CAD/` | SolidCraft models (`NEREIDE.solidcraft`, `NEREIDE_con_base.solidcraft`), STEP files, renders, 2D sheets and DXF views. `NAIADE_*` files are the earlier name of the project |
| `schemi_funzionali/` | Source and output of the functional diagrams (`genera_schemi.py`, Graphviz) |
| `sim/` | The flight simulation (see below) |
| `CONSEGNA_TEAM_26/` | The delivery folder |
| `HANDOFF_NEREIDE.md` | Project status and decisions (in Italian) |
| `NEREIDE.step`, `NEREIDE_con_base.step` | CAD exports |
| `TEAM_26.pptx`, `Sketches_Graphic tables_team_26.pdf` | Working copies of the presentation and drawing sheets |

## The simulation (`sim/`)

PX4 SITL + Gazebo Harmonic + ROS 2 Jazzy, with the aircraft built from the team's CAD. The full demo mission is flown by a script: take-off from the docking station, cruise to a lake 1 km away, hover at 10 m with the probe lowered 9.6 m, return, landing within 10 cm of the base centre, samples to the fridge and battery swap. The scene is placed at Lago di Candia (TO), so QGroundControl shows a real map.

| Item | Where |
|---|---|
| Parameters and results | `PARAMETRI_SIMULAZIONE.md` |
| Every test with its outcome and what was learned | `TEST_LOG.md` (30+ flights) |
| Aircraft model generated from the CAD | `export_meshes.py` (STEP → meshes), `gen_sdf.py` (model), `naiade/`, `4050_gz_naiade` (PX4 airframe) |
| World and docking station | `worlds/nereide.sdf`, `models/docking_station/` |
| Mission and launcher | `mission_nereide.py`, `run_mission.sh` |
| Analysis | `analyze_log.py`, `analyze_trans.py`, `report_plots.py`, `check_clearance.py`, `report/` |
| Video tools | `edit_video_en.py`, `edit_prototype_video.py`, `place_windows.py` |
| PX4 changes | `px4_tiltwing.patch` |

**Two PX4 code changes were needed to fly a tilt-wing:**
1. `VT_BT_TW_KEEP`: when returning to hover, standard PX4 idles the motors while the wings rotate and the aircraft would fall; the patch keeps thrust and control active.
2. Yaw saturation: with symmetric wings the tilt cannot control yaw, and PX4 reported yaw as always saturated, so the aircraft kept spinning; fixed in the control allocator.

**Running it** (needs PX4-Autopilot cloned in `~/PX4-Autopilot` with the patch applied, Gazebo Harmonic, ROS 2 Jazzy, and a Python venv with `pyulog`, `pymavlink`, `trimesh`, `cadquery-ocp`, `imageio-ffmpeg`):

```
sim/run_mission.sh                 # demo with the Gazebo window, real time
FAST=1 sim/run_mission.sh          # quick test, no window, ~2 minutes
MAP=1 sim/run_mission.sh           # also opens QGroundControl
VIDEO=1 MAP=1 sim/run_mission.sh   # records and edits the video
```

### Simulation vs team sizing

| | Simulated | Team sizing | Why |
|---|---|---|---|
| Hover | 3.7 kW | 3.4 kW | propeller figure of merit 0.7 instead of 0.8 |
| Cruise at 75 km/h | 1.0 kW | 0.46 kW | simplified flat-plate aerodynamics: lift-to-drag 7 instead of 14 |

The simulation is the conservative case. Masses, inertias and aerodynamic coefficients are estimates, not measurements; there is no CFD, and the docking station is simplified.

## Not included

Flight logs (3.8 GB), the prototype video, the TiltOne paper and the ID.pdf rules (third-party material).
