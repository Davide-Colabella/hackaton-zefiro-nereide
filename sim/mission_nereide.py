"""Missione dimostrativa NEREIDE: decollo dalla base, crociera ad ala fissa, hovering a 10 m sul lago,
sonda calata col verricello, rientro, scarico campioni e cambio batteria alla docking station.
Va lanciato a simulazione avviata (sim/run_mission.sh). Coordinate in metri ENU rispetto alla base (x est, y nord)."""
import math, os, sys, threading, time
sys.path.append("/usr/lib/python3/dist-packages")  # binding gz-transport di sistema
from gz.transport13 import Node
from gz.msgs10.double_pb2 import Double
os.environ.setdefault("MAVLINK20", "1")  # serve per mission_type e i campi estesi
from pymavlink import mavutil

LAKE = (1000.0, 0.0)
HOVER_ALT = 10.0          # sopra l'acqua (slide 7)
CRUISE_ALT = 40.0          # sopra gli edifici più alti (25 m)
PROBE_DROP = 9.6          # la sonda tocca l'acqua: origine drone a 10 m, punta sonda 0.73 m sotto
N_SEG = 34                # segmenti del cavo, come in gen_sdf.py
M = mavutil.mavlink


NODE, PUBS = Node(), {}


def gz(topic, value):
    # publisher persistenti: `gz topic` da riga di comando costa ~0.5 s a chiamata
    if topic not in PUBS:
        PUBS[topic] = NODE.advertise(topic, Double)
        time.sleep(0.3)  # tempo per la scoperta del subscriber
    PUBS[topic].publish(Double(data=value))


def ramp(target, start, seconds, sim_speed):
    # muove sonda e cavo insieme a velocità costante (il controllore di giunto da solo sarebbe un gradino)
    steps = max(1, int(seconds * 4))
    for i in range(1, steps + 1):
        d = start + (target - start) * i / steps
        gz("/model/naiade_0/winch", -d)
        gz("/model/naiade_0/winch_cable", -d / N_SEG)
        time.sleep(seconds / steps / sim_speed)


def probe_cycle(sim_speed):
    say("hovering a 10 m sul lago: cala la sonda")
    ramp(PROBE_DROP, 0, 10, sim_speed)
    say("sonda in acqua: analisi e prelievo di un flacone")
    time.sleep(10 / sim_speed)
    ramp(0, PROBE_DROP, 10, sim_speed)
    say("sonda recuperata, rientro")


EVENTS = os.environ.get("NEREIDE_EVENTS")  # file con l'orario di ogni fase, per il montaggio del video


def say(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
    if EVENTS:
        with open(EVENTS, "a") as f:
            f.write(f"{time.time():.2f}\t{msg}\n")


def main():
    sim_speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    # link GCS di PX4 (porta 14550): quello onboard (14540) non risponde al protocollo missione
    mav = mavutil.mavlink_connection(f"udpin:0.0.0.0:{os.environ.get('NEREIDE_MAV_PORT', '14550')}", source_system=255, source_component=190)
    mav.wait_heartbeat()
    # la posizione globale arriva a 0,0 finché l'EKF non ha l'origine: aspetto la home vera
    home = None
    while home is None or home.latitude == 0:
        mav.mav.command_long_send(1, 1, M.MAV_CMD_GET_HOME_POSITION, 0, 0, 0, 0, 0, 0, 0, 0)
        home = mav.recv_match(type="HOME_POSITION", blocking=True, timeout=3)
    lat0, lon0 = home.latitude / 1e7, home.longitude / 1e7
    say(f"home {lat0:.6f} {lon0:.6f}")

    def ll(x, y):
        return (int((lat0 + y / 111320.0) * 1e7), int((lon0 + x / (111320.0 * math.cos(math.radians(lat0)))) * 1e7))

    REL = M.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT
    items = [  # (comando, x, y, quota, param1..4); rotta dritta base -> lago -> base, senza giri
        # destinazione del decollo a metà strada: puntata sul lago faceva sorpassare il punto di frenata e tornare indietro
        (M.MAV_CMD_NAV_VTOL_TAKEOFF, 300, 0, 20, (0, 0, 0, math.nan)),
        (M.MAV_CMD_NAV_WAYPOINT, LAKE[0] - 100, 0, CRUISE_ALT, (0, 0, 0, math.nan)),
        (M.MAV_CMD_DO_VTOL_TRANSITION, 0, 0, 0, (M.MAV_VTOL_STATE_MC, 0, 0, 0)),          # frenata ~60 m a 3 m/s²
        (M.MAV_CMD_NAV_WAYPOINT, *LAKE, HOVER_ALT, (0, 0, 0, math.nan)),
        (M.MAV_CMD_NAV_LOITER_TIME, *LAKE, HOVER_ALT, (42, 0, 0, math.nan)),   # sonda e prelievo: 30 s + margine
        # risale e si gira verso la base (yaw NED 270° = ovest) prima della transizione: niente giro largo
        (M.MAV_CMD_NAV_WAYPOINT, *LAKE, 40, (0, 0, 0, 270)),
        (M.MAV_CMD_DO_VTOL_TRANSITION, 0, 0, 0, (M.MAV_VTOL_STATE_FW, 0, 0, 0)),
        (M.MAV_CMD_NAV_WAYPOINT, 120, 0, CRUISE_ALT, (0, 0, 0, math.nan)),
        (M.MAV_CMD_DO_VTOL_TRANSITION, 0, 0, 0, (M.MAV_VTOL_STATE_MC, 0, 0, 0)),
        # arriva sopra la base col muso in avanti (ovest, 270°), poi ruota sul posto verso est (90°)
        # come la docking station: pattini allineati alle guide a cono
        (M.MAV_CMD_NAV_WAYPOINT, 0, 0, 15, (0, 0, 0, 270)),
        (M.MAV_CMD_NAV_WAYPOINT, 0, 0, 15, (0, 0, 0, 90)),
        (M.MAV_CMD_NAV_LAND, 0, 0, 0, (0, 0, 0, 90)),
    ]
    LOITER = 4
    mav.mav.mission_count_send(1, 1, len(items), M.MAV_MISSION_TYPE_MISSION)
    sent = set()
    while len(sent) < len(items):
        req = mav.recv_match(type=["MISSION_REQUEST_INT", "MISSION_REQUEST", "MISSION_ACK"], blocking=True, timeout=10)
        assert req is not None and req.get_type() != "MISSION_ACK", f"caricamento missione fallito dopo {len(sent)} item: {req}"
        cmd, x, y, alt, p = items[req.seq]
        do = cmd == M.MAV_CMD_DO_VTOL_TRANSITION  # i comandi DO non hanno posizione
        lat, lon = (0, 0) if do else ll(x, y)
        frame = M.MAV_FRAME_MISSION if do else REL
        mav.mav.mission_item_int_send(1, 1, req.seq, frame, cmd, 0, 1, *p, lat, lon, alt, M.MAV_MISSION_TYPE_MISSION)
        sent.add(req.seq)
    ack = mav.recv_match(type="MISSION_ACK", blocking=True, timeout=10)
    assert ack and ack.type == M.MAV_MISSION_ACCEPTED, f"missione rifiutata: {ack}"
    say(f"missione caricata ({len(items)} item)")

    for _ in range(30):  # l'arming può essere rifiutato finché l'EKF non converge
        mav.mav.command_long_send(1, 1, M.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
        a = mav.recv_match(type="COMMAND_ACK", blocking=True, timeout=3)
        if a and a.command == M.MAV_CMD_COMPONENT_ARM_DISARM and a.result == 0:
            break
        time.sleep(2 / sim_speed)
    mav.mav.command_long_send(1, 1, M.MAV_CMD_MISSION_START, 0, 0, 0, 0, 0, 0, 0, 0)
    say("decollo: ali verticali, 8 eliche verso l'alto")

    seq, probe, vtol = -1, None, 0
    while True:
        msg = mav.recv_match(type=["MISSION_CURRENT", "EXTENDED_SYS_STATE", "STATUSTEXT"], blocking=True, timeout=30)
        if msg is None:
            continue
        if msg.get_type() == "STATUSTEXT":
            say("PX4: " + msg.text)
        elif msg.get_type() == "MISSION_CURRENT" and msg.seq != seq:
            seq = msg.seq
            say(f"item {seq}")
            if seq == LOITER and probe is None:
                probe = threading.Thread(target=probe_cycle, args=(sim_speed,))
                probe.start()  # in parallelo: il ciclo MAVLink deve continuare a leggere
        elif msg.get_type() == "EXTENDED_SYS_STATE":
            # istanti delle transizioni: servono al montaggio per didascalie sincronizzate
            if msg.vtol_state != vtol:
                vtol = msg.vtol_state
                say({1: "vtol: transizione verso FW", 2: "vtol: transizione verso MC", 3: "vtol: MC", 4: "vtol: FW"}.get(vtol, f"vtol {vtol}"))
            if probe and not probe.is_alive() and msg.landed_state == M.MAV_LANDED_STATE_ON_GROUND:
                break
    say("atterrato sulla base: guide a cono e contatti")
    time.sleep(1.5 / sim_speed)
    say("scarico campioni nel frigo a 4 °C")
    gz("/model/naiade_0/carousel", -0.45); gz("/model/docking_station/sample_lift", -0.33)
    time.sleep(4 / sim_speed)
    gz("/model/naiade_0/carousel", 0); gz("/model/docking_station/sample_lift", 0)
    time.sleep(3 / sim_speed)
    say("cambio batteria: l'elevatore sfila la cartuccia scarica")
    gz("/model/naiade_0/battery", -0.10)
    time.sleep(1.5 / sim_speed)
    gz("/model/naiade_0/battery", -0.50); gz("/model/docking_station/elevator", -0.40)
    time.sleep(4 / sim_speed)
    say("inserita la cartuccia carica dal magazzino")
    gz("/model/naiade_0/battery", 0); gz("/model/docking_station/elevator", 0)
    time.sleep(4 / sim_speed)
    say("pronto a ripartire")


if __name__ == "__main__":
    main()
