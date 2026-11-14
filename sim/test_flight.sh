#!/usr/bin/env bash
# Volo di prova headless accelerato: decollo, hover, (opz.) transizione. Stampa lo stato ogni 2 s simulati.
# Demo con finestra: HEADLESS= SPEED=1 sim/test_flight.sh 20 transition land
# Uso: [SPEED=5] [PARAMS="MC_PITCHRATE_P=0.5 VT_TILT_TRANS=0.9"] sim/test_flight.sh [secondi_hover] [transition] [land]
HOVER=${1:-20}; SPEED=${SPEED:-5}
B=~/PX4-Autopilot/build/px4_sitl_default/bin
w() { sleep "$(awk "BEGIN{print $1/$SPEED}")"; }   # attesa in secondi simulati
stop() { pkill -x px4; pkill -f "^gz sim"; pkill -x ruby; pkill -x MicroXRCEAgent; pkill -f "^tail -f /dev/null"; true; }
cd ~/PX4-Autopilot || exit 1
stop; sleep 1
rm -f build/px4_sitl_default/rootfs/fs/parameters*.bson  # riparte dai default dell'airframe
# stdin aperto: con /dev/null la console pxh va in loop
(tail -f /dev/null | HEADLESS=${HEADLESS-1} PX4_SIM_SPEED_FACTOR=$SPEED make px4_sitl gz_naiade >/tmp/naiade_test.log 2>&1 &)
until grep -q "Startup script returned successfully" /tmp/naiade_test.log; do sleep 0.5; done
cd build/px4_sitl_default
# il fattore richiesto non sempre è raggiunto (dipende dal modello): attese calcolate su quello misurato
RTF=$(timeout 8 gz topic -e -t /stats -n 5 2>/dev/null | awk '/real_time_factor/{s+=$2; n++} END{print (n ? s/n : 1)}')
SPEED=$(awk "BEGIN{r=$RTF; print (r > 0.2 ? r : 1)}"); echo "fattore tempo reale misurato: $SPEED"
for kv in $PARAMS; do $B/px4-param set "${kv%%=*}" "${kv#*=}" | tail -1; done
w 15
sample() {
  for _ in $(seq 1 "$1"); do
    a=$($B/px4-listener vehicle_attitude -n 1 | grep -o "Roll.*")
    z=$($B/px4-listener vehicle_local_position -n 1 | grep -E "^\s+(z|vx|vy):" | tr -s ' ' | tr '\n' ' ')
    s=$($B/px4-listener airspeed_validated -n 1 | grep calibrated_airspeed_m_s | tr -s ' ')
    echo "$a |$z|$s"; w 2
  done
}
$B/px4-commander takeoff; sample $((HOVER / 2))
if [ "$2" = transition ]; then
  $B/px4-commander transition; sample 25
  $B/px4-listener vehicle_status -n 1 | grep -E "vehicle_type|in_transition_mode"
fi
if [ "$3" = land ]; then
  echo "--- ritorno in hover"; $B/px4-commander transition; sample 8
  echo "--- atterraggio"; $B/px4-commander land; sample 12
  $B/px4-listener vehicle_land_detected -n 1 | grep -E "^\s+landed:"
fi
grep -aE "WARN|ERROR" /tmp/naiade_test.log | grep -vE "GCS|heading reference|height estimate|Airspeed selector|param_get|param 65535|FD_ACT" | tail -5
L=$(ls -t rootfs/fs/log/*/*.ulg | head -1); cp "$L" ~/Documenti/hackaton_zefiro/sim/logs/; echo "log: $(basename "$L")"
[ -n "$KEEP" ] || stop  # KEEP=1 lascia aperta la finestra a fine volo
