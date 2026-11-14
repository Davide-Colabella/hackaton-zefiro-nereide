#!/usr/bin/env bash
# Missione dimostrativa NEREIDE nel mondo con lago e docking station.
# Uso: sim/run_mission.sh            (finestra Gazebo, tempo reale)
#      VIDEO=1 sim/run_mission.sh    (finestra + registrazione mp4 in sim/video/, accelerata 2x per la slide)
#      FAST=1 sim/run_mission.sh     (test rapido: senza finestra, senza cavo, ~2 min)
#      MAP=1 ...                     (apre anche QGroundControl con la mappa)
SIM=$(cd "$(dirname "$0")" && pwd)
PX4=~/PX4-Autopilot
SPEED=${SPEED:-1}
if [ -n "$FAST" ]; then HEADLESS=1; SPEED=10; fi
if [ -n "$VIDEO" ]; then SPEED=${VIDEO_SPEED:-2}; fi
NO_CABLE=$FAST python3 "$SIM/gen_sdf.py" >/dev/null
stop() { pkill -f "[Q]GroundControl"; pkill -x px4; pkill -f "^gz sim"; pkill -x ruby; pkill -x MicroXRCEAgent; pkill -f "^tail -f /dev/null"; true; }
stop; sleep 1
ln -sfn "$SIM/worlds/nereide.sdf" "$PX4/Tools/simulation/gz/worlds/nereide.sdf"
rm -f "$PX4"/build/px4_sitl_default/rootfs/fs/parameters*.bson
export GZ_SIM_RESOURCE_PATH="$SIM/models:$GZ_SIM_RESOURCE_PATH"
export PX4_GZ_WORLD=nereide PX4_GZ_MODEL_POSE="0,0,0.80,0,0,0" PX4_SIM_SPEED_FACTOR=$SPEED
cd "$PX4" || exit 1
# in modalità video la finestra la apro io, con la configurazione che include il registratore
GUI_BY_PX4=${HEADLESS-}; [ -n "$VIDEO" ] && GUI_BY_PX4=1
# stdin aperto: con /dev/null la console pxh va in loop
(tail -f /dev/null | HEADLESS=$GUI_BY_PX4 make px4_sitl gz_naiade >/tmp/nereide_sim.log 2>&1 &)
until grep -q "Startup script returned successfully" /tmp/nereide_sim.log; do sleep 0.5; done
if [ -n "$VIDEO" ]; then
  mkdir -p "$SIM/video"
  OUT="$SIM/video/nereide_missione_$(date +%H%M)"
  export NEREIDE_EVENTS="$OUT.eventi.tsv"; rm -f "$NEREIDE_EVENTS"
  (gz sim -g --gui-config "$SIM/gui_video.config" >/tmp/nereide_gui.log 2>&1 &)
  # il plugin VideoRecorder di Gazebo non si carica: registro la finestra con ffmpeg (x11grab)
  until xwininfo -name "Gazebo Sim" >/dev/null 2>&1; do sleep 0.5; done
  sleep 6  # la scena deve finire di caricare
  # camera che segue il drone; pgain 0.5 (default 0.01): a 25 m/s il drone altrimenti esce dall'inquadratura
  gz topic -t /gui/track -m gz.msgs.CameraTrack -p 'track_mode: FOLLOW, follow_target: {name: "naiade_0"}, follow_offset: {x: -5, y: -5, z: 2.5}, follow_pgain: 1.0'
  FFMPEG=$(~/.venvs/cad/bin/python -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())")
fi
# canale MAVLink dedicato allo script (14559): la 14550 resta libera per QGroundControl (mappa)
build/px4_sitl_default/bin/px4-mavlink stop -u 13030 >/dev/null  # istanza gimbal inutilizzata: PX4 ha un massimo di istanze
build/px4_sitl_default/bin/px4-mavlink start -u 14558 -o 14559 -r 400000 >/dev/null
export NEREIDE_MAV_PORT=14559
if [ -n "$MAP" ]; then
  # sg: prende il gruppo dialout senza rifare il login (evita l avviso sui permessi seriali)
  QGC=~/Applicazioni/qgc/squashfs-root/AppRun
  if id -nG "$USER" | grep -qw dialout || getent group dialout | grep -qw "$USER"; then (sg dialout -c "$QGC" >/tmp/qgc.log 2>&1 &); else ("$QGC" >/tmp/qgc.log 2>&1 &); fi
  until xwininfo -root -tree | grep -q '"QGroundControl'; do sleep 0.5; done; sleep 8
fi
if [ -n "$VIDEO" ]; then
  # Gazebo sui 2/3 sinistri a tutta altezza, QGroundControl sul terzo destro
  [ -n "$MAP" ] && ~/.venvs/cad/bin/python "$SIM/place_windows.py" && sleep 2
  read X Y W H < <(xwininfo -name "Gazebo Sim" | awk '/Absolute upper-left X/{x=$4} /Absolute upper-left Y/{y=$4} /Width/{w=$2} /Height/{h=$2} END{print x, y, w, h}')
  # x11grab non cattura fuori schermo: limito alla parte visibile
  read SW SH < <(xwininfo -root | awk '/Width/{w=$2} /Height/{h=$2} END{print w, h}')
  X=$((X < 0 ? 0 : X)); Y=$((Y < 0 ? 0 : Y)); W=$((X + W > SW ? SW - X : W)); H=$((Y + H > SH ? SH - Y : H)); W=$((W - W % 2)); H=$((H - H % 2))
  "$FFMPEG" -y -loglevel error -f x11grab -framerate 30 -video_size ${W}x${H} -i "$DISPLAY+$X,$Y" \
    -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p "$OUT.grezzo.mp4" </dev/null &
  CROP="$((W - 30)):$((H - 116)):15:97"; echo "$CROP" > "$OUT.crop"  # scena 3D senza barra del titolo e bordi
  FF_PID=$!; REC_START=$(date +%s.%N); echo "$REC_START" > "$OUT.inizio"; echo "registrazione: $OUT.grezzo.mp4 (${W}x${H})"
  if [ -n "$MAP" ]; then  # seconda cattura: la mappa, sovrapposta nel montaggio
    QID=$(xwininfo -root -tree | grep '"QGroundControl' | head -1 | awk '{print $1}')
    read QX QY QW QH < <(xwininfo -id $QID | awk '/Absolute upper-left X/{x=$4} /Absolute upper-left Y/{y=$4} /Width/{w=$2} /Height/{h=$2} END{print x, y, w, h}')
    # x11grab non cattura fuori schermo: limito la regione alla parte visibile della finestra
    read SW SH < <(xwininfo -root | awk '/Width/{w=$2} /Height/{h=$2} END{print w, h}')
    QX=$((QX < 0 ? 0 : QX)); QY=$((QY < 0 ? 0 : QY)); QW=$((QX + QW > SW ? SW - QX : QW)); QH=$((QY + QH > SH ? SH - QY : QH))
    QW=$((QW - QW % 2)); QH=$((QH - QH % 2))
    "$FFMPEG" -y -loglevel error -f x11grab -framerate 30 -video_size ${QW}x${QH} -i "$DISPLAY+$QX,$QY" \
      -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$OUT.mappa.mp4" </dev/null &
    QFF_PID=$!; echo "$(date +%s.%N)" > "$OUT.mappa.inizio"
  fi
fi
RTF=$(timeout 8 gz topic -e -t /stats -n 5 2>/dev/null | awk '/real_time_factor/{s+=$2; n++} END{print (n ? s/n : 1)}')
echo "fattore tempo reale: $RTF"
~/.venvs/cad/bin/python -I "$SIM/mission_nereide.py" "$RTF"
if [ -n "$VIDEO" ]; then
  kill -INT $FF_PID ${QFF_PID:-}; wait $FF_PID ${QFF_PID:-} 2>/dev/null
  MAPPA=""; [ -n "${QFF_PID:-}" ] && MAPPA="$OUT.mappa.mp4 $(cat "$OUT.mappa.inizio")"
  # montaggio a velocità variabile: 30-60 s per la slide
  SIM_RTF=$RTF ~/.venvs/cad/bin/python -I "$SIM/edit_video_en.py" "$OUT"  # versione inglese per la slide 10
  ~/.venvs/cad/bin/python -I "$SIM/edit_video.py" "$OUT.grezzo.mp4" "$NEREIDE_EVENTS" "$REC_START" "$OUT.mp4" "$CROP" $MAPPA
fi
L=$(ls -t build/px4_sitl_default/rootfs/fs/log/*/*.ulg | head -1); cp "$L" "$SIM/logs/"; echo "log: $(basename "$L")"
[ -n "$HEADLESS" ] && stop
true
