"""Sovraimpressioni in inglese sul video del modellino (stile del video di simulazione: barra nera con filo giallo).
Uso: edit_prototype_video.py ingresso.mp4 uscita.mp4"""
import subprocess, sys
import imageio_ffmpeg

src, out = sys.argv[1], sys.argv[2]
FONT, FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# (inizio s, fine s, titolo, sottotitolo): tempi ricavati dai fotogrammi, da verificare sull'audio
CAPTIONS = [
    (0, 6, "NEREIDE · Team 26", "Tilt-wing box-wing eVTOL for urban water monitoring"),
    (6, 12, "The concept", "Flies like an aeroplane over rivers, lakes and coasts"),
    (12, 36, "Mission", "Analyse the water on site or take samples, then return to base"),
    (36, 54, "1:5 scale model", "Two staggered wings joined at the tips: the box wing"),
    (54, 60, "Solar base", "Samples to the 4 °C fridge, battery swapped in under 2 minutes"),
    (60, 72, "Tilting wings", "Wings at 90° to hover, horizontal to cruise, with all 8 propellers"),
    (72, 84, "Winch and probe", "The probe is lowered on its line while the eVTOL hovers"),
    (84, 108, "Simulation · ROS 2 · Gazebo · PX4", "The full mission flown in software, from take-off to battery swap"),
    (108, 120, "Simulation results", "Hover 3.7 kW · thrust / weight 2.3 · landing < 10 cm off centre"),
    (120, 126, "Cruise and hover", "Same aircraft, two flight modes"),
    (126, 168, "Winch demonstration", "In the real mission the probe goes 9.6 m down into the water"),
    (168, 186, "Docking station", "Guided landing, data download, samples to the fridge, new battery"),
    (186, 200, "Model features", "Tilting wings, winch with probe, removable battery cartridge"),
    (200, 213, "Thank you", "NEREIDE · Team 26 · IBEC Innovative Design"),
]
esc = lambda t: t.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace("%", r"\%")
f = ["scale=1920:1080,fps=30",
     # etichetta fissa in alto a sinistra
     "drawbox=x=36:y=36:w=470:h=52:color=0x111111@0.85:t=fill,drawbox=x=36:y=36:w=6:h=52:color=0xF5C400:t=fill",
     f"drawtext=fontfile={FONT}:text='NEREIDE · 1\\:5 SCALE MODEL':fontcolor=0xF5C400:fontsize=26:x=56:y=50"]
for a, b, title, sub in CAPTIONS:
    en = f"enable='between(t,{a},{b})'"
    f += [f"drawbox=x=0:y=ih-150:w=iw:h=150:color=0x111111@0.88:t=fill:{en}",
          f"drawbox=x=0:y=ih-150:w=iw:h=5:color=0xF5C400:t=fill:{en}",
          f"drawtext=fontfile={FONT}:text='{esc(title)}':fontcolor=0xF5C400:fontsize=40:x=48:y=h-122:{en}",
          f"drawtext=fontfile={FONT_R}:text='{esc(sub)}':fontcolor=white:fontsize=34:x=48:y=h-66:{en}"]
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", src, "-vf", ",".join(f),
                "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
print("video:", out)
