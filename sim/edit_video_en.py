"""Montaggio del video per la slide 10 (inglese, stile HANDOFF): 7 fasi sincronizzate con gli eventi della missione,
velocità di riproduzione indicata, riquadro dati, mappa QGroundControl in basso a destra, schermata finale.
Uso: edit_video_en.py <prefisso>   (es. sim/video/nereide_missione_1720 -> usa .grezzo.mp4 .eventi.tsv .inizio [.mappa.*])"""
import os, subprocess, sys
import imageio_ffmpeg

pre = sys.argv[1]
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
rec0 = float(open(pre + ".inizio").read())
ev = [(float(t) - rec0, m) for t, m in (l.rstrip("\n").split("\t", 1) for l in open(pre + ".eventi.tsv"))]


def at(key, n=1):  # n-esima occorrenza dell'evento
    return [t for t, m in ev if key in m][n - 1]


mappa = None
if os.path.exists(pre + ".mappa.mp4"):
    mappa = float(open(pre + ".mappa.inizio").read()) - rec0
CROP = "crop=" + (open(pre + ".crop").read().strip() if os.path.exists(pre + ".crop") else "1278:750:15:97")

# (inizio, fine, durata nel video [s], didascalia, riquadro dati)
phases = [
    (at("decollo"), at("vtol: FW", 1), 8, "1  Vertical take-off and transition", "wings 90° → 0°  ·  8 rotors lift 245 N"),
    (at("vtol: FW", 1), at("transizione verso MC", 1), 6, "2  Cruise on the wing", "75 km/h  ·  40 m  ·  rotors only push"),
    (at("transizione verso MC", 1), at("cala la sonda"), 6, "3  Braking over the lake", "wings tilt back up  ·  3 m/s²"),
    (at("cala la sonda"), at("sonda recuperata"), 9, "4  Hover at 10 m: probe into the water", "winch 9.6 m  ·  pH, T, O₂, turbidity"),
    (at("sonda recuperata"), at("transizione verso MC", 2), 7, "5  Climb, transition and return", "1 km back to base  ·  straight line"),
    (at("transizione verso MC", 2), at("atterrato"), 7, "6  Guided landing on the base", "nose aligned to the cones  ·  < 10 cm"),
    (at("atterrato"), at("pronto"), 7, "7  Samples to the fridge, battery swap", "4 °C  ·  fresh cartridge in < 2 min"),
]
esc = lambda t: t.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace("%", r"\%")
parts, labels = [], []
for i, (a, b, target, title, data) in enumerate(phases):
    k = max((b - a) / target, 1.0)
    # il grezzo è già accelerato dalla simulazione (~2x): la velocità totale tiene conto del fattore reale
    pill = f"{round(k * float(os.environ.get('SIM_RTF', 2)))}× SPEED · video sped up"
    v = f"[0:v]trim={a:.2f}:{b:.2f},setpts=(PTS-STARTPTS)/{k:.4f},fps=30,{CROP}"
    if mappa is not None:
        parts.append(f"[1:v]trim={max(a - mappa, 0):.2f}:{b - mappa:.2f},setpts=(PTS-STARTPTS)/{k:.4f},fps=30,scale=320:-2,"
                     f"pad=iw+6:ih+6:3:3:color=0xF5C400[m{i}]")
        v += f"[g{i}];[g{i}][m{i}]overlay=W-w-18:18"
    v += (f",drawbox=x=0:y=ih-86:w=iw:h=86:color=0x111111@0.92:t=fill,drawbox=x=0:y=ih-86:w=iw:h=4:color=0xF5C400:t=fill,"
          f"drawtext=fontfile={FONT}:text='{esc(title)}':fontcolor=white:fontsize=30:x=28:y=h-62,"
          f"drawbox=x=18:y=18:w=560:h=46:color=0x111111@0.85:t=fill,drawbox=x=18:y=18:w=6:h=46:color=0xF5C400:t=fill,"
          f"drawtext=fontfile={FONT_R}:text='{esc(data)}':fontcolor=0xF5C400:fontsize=20:x=36:y=31,"
          f"drawtext=fontfile={FONT}:text='{esc(pill)}':fontcolor=0x111111:fontsize=18:box=1:boxcolor=0xF5C400:boxborderw=8:"
          f"x=w-text_w-26:y={'h-128' if mappa is not None else '26'}[v{i}]")
    parts.append(v); labels.append(f"[v{i}]")
    print(f"{title}: {b - a:5.1f} s -> {(b - a) / k:4.1f} s  ({pill})")

# schermata finale con i dati (5 s)
rows = ["NEREIDE · PX4 + Gazebo + ROS 2", "25 kg  ·  8 × Ø450 mm  ·  T/W 2.3",
        "Cruise 75 km/h  ·  hover 10 m over the lake", "1 km out and back  ·  landing < 10 cm off centre",
        "Probe 9.6 m down  ·  battery swap at the base"]
W_, H_ = CROP[5:].split(":")[:2]
card = f"color=c=0x111111:s={W_}x{H_}:d=5:r=30,drawbox=x=0:y=0:w=iw:h=8:color=0xF5C400:t=fill"
for j, r in enumerate(rows):
    card += f",drawtext=fontfile={FONT if j == 0 else FONT_R}:text='{esc(r)}':fontcolor={'0xF5C400' if j == 0 else 'white'}:fontsize={36 if j == 0 else 28}:x=(w-text_w)/2:y={170 + j * 90}"
parts.append(card + "[vend]"); labels.append("[vend]")

graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=0[out]"
inputs = ["-i", pre + ".grezzo.mp4"] + (["-i", pre + ".mappa.mp4"] if mappa is not None else [])
out = pre + "_EN.mp4"
subprocess.run([FF, "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", out], check=True)
print("video:", out)
