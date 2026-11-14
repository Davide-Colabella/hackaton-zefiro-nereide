"""Affianca le finestre per la registrazione: Gazebo sui 2/3 sinistri dell'area utile, QGroundControl sul terzo destro."""
import time
from ewmh import EWMH

e = EWMH()
x0, y0, W, H = e.getWorkArea()[:4]  # area utile senza barra in alto e dock


def find(title):
    for _ in range(60):
        for w in e.getClientList():
            name = (e.getWmName(w) or b"").decode(errors="ignore")
            if name.startswith(title):
                return w
        time.sleep(0.5)
    raise SystemExit(f"finestra '{title}' non trovata")


for title, x, w in (("Gazebo Sim", x0, W * 2 // 3), ("QGroundControl", x0 + W * 2 // 3, W - W * 2 // 3)):
    win = find(title)
    e.setWmState(win, 0, "_NET_WM_STATE_MAXIMIZED_VERT"); e.setWmState(win, 0, "_NET_WM_STATE_MAXIMIZED_HORZ")
    e.setMoveResizeWindow(win, gravity=0, x=x, y=y0, w=w, h=H)
    e.setActiveWindow(win)
e.display.flush()
print("finestre affiancate:", x0, y0, W, H)
