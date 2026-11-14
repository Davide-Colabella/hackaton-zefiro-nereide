"""Monta il video della missione a velocità variabile per la slide (30-60 s):
crociera molto accelerata, sonda e cambio batteria più lenti, con didascalia per ogni fase.
Uso: edit_video.py grezzo.mp4 eventi.tsv inizio_registrazione_epoch uscita.mp4 [crop w:h:x:y]"""
import subprocess, sys
import imageio_ffmpeg

raw, events_file, rec_start, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
# la cattura x11grab prende anche barra del titolo e bordi: tengo solo la scena 3D
crop = f"crop={sys.argv[5]}," if len(sys.argv) > 5 else ""
# opzionale: cattura della mappa di QGroundControl (file, inizio epoch) sovrapposta in basso a destra
mappa = (sys.argv[6], float(sys.argv[7]) - rec_start) if len(sys.argv) > 7 else None
ev = [(float(t) - rec_start, m) for t, m in (l.rstrip("\n").split("\t", 1) for l in open(events_file))]
at = lambda key: next(t for t, m in ev if key in m)

# (inizio, fine, durata voluta nel video [s], didascalia)
cuts = [
    (at("decollo"), at("cala la sonda"), 16, "Decollo verticale, transizione e crociera a 90 km/h"),
    (at("cala la sonda"), at("sonda recuperata"), 10, "Hovering a 10 m: la sonda scende in acqua"),
    (at("sonda recuperata"), at("atterrato"), 14, "Rientro ad ala fissa e atterraggio sulla base"),
    (at("atterrato"), at("pronto"), 10, "Campioni nel frigo a 4 °C e cambio batteria"),
]
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
parts = []
for i, (a, b, target, text) in enumerate(cuts):
    k = max((b - a) / target, 1.0)  # mai rallentare oltre il tempo reale
    txt = text.replace(":", r"\:").replace("'", r"\'")
    base = f"[0:v]trim={a:.2f}:{b:.2f},setpts=(PTS-STARTPTS)/{k:.3f},fps=30,{crop}"
    if mappa:  # stessa finestra temporale sulla cattura della mappa (partita mappa[1] s dopo)
        ma, mb = max(a - mappa[1], 0), b - mappa[1]
        parts.append(f"[1:v]trim={ma:.2f}:{mb:.2f},setpts=(PTS-STARTPTS)/{k:.3f},fps=30,scale=420:-2[m{i}]")
        base = base.rstrip(",") + f"[g{i}];[g{i}][m{i}]overlay=W-w-16:H-h-16,"
    parts.append(base + f"drawtext=fontfile={font}:text='{txt}':fontcolor=white:fontsize=34:box=1:boxcolor=0x0d1b24@0.75:"
                 f"boxborderw=14:x=(w-text_w)/2-200*{1 if mappa else 0}:y=h-90[v{i}]")
    print(f"{text}: {b - a:5.1f} s reali -> {(b - a) / k:4.1f} s (x{k:.1f})")
graph = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(cuts))) + f"concat=n={len(cuts)}:v=1:a=0[out]"
inputs = ["-i", raw] + (["-i", mappa[0]] if mappa else [])
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
                "-map", "[out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out], check=True)
print("video:", out)
