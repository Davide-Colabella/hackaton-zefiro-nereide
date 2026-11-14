# HANDOFF — NEREIDE (IBEC · Innovative Design · Team 26)

Stato al **14/11/2026, 17:00**. Questo file sostituisce `HANDOFF_NAIADE.md`, che resta come storico (decisioni iniziali, ricerca fonti, docking station).

---

## 1. In breve

**NEREIDE** (prima "NAIADE") è un **eVTOL tilt-wing ad ala a scatola** per monitorare fiumi, laghi e coste urbane.
- Vola come un aereo e si ferma in hovering a ~10 m.
- **Analizza** l'acqua sul posto con una sonda calata dal verricello, oppure **preleva** un campione.
- Torna a una **base solare** che mette i campioni in frigo a 4 °C e **cambia la batteria** in meno di 2 minuti.

Dal TiltOne (Palaia et al. 2021, [1]) è presa **solo l'architettura**. Missione, moduli, verricello, base, dimensionamento e CAD sono del team.

### Regole da rispettare
- **Non chiamarlo mai "drone"**: è un eVTOL o "il velivolo".
- **Massimo 10 slide** (−5 punti per ogni slide in più). Niente tavole CAD 2D nelle slide.
- Video massimo **4 minuti**.
- Il PDF da consegnare va chiamato **`26.pdf`** (non ancora fatto).
- **Tutto in inglese.** La versione italiana è stata sostituita, non duplicata. La guida alla presentazione è l'unica in italiano, perché è a uso interno.
- Nessuna comunicazione con persone fuori dal team. Nessun dato personale verso servizi esterni.
- Riferimenti [1]–[4] **solo in copertina**.
- Le Nereidi sono **ninfe**, figlie di Nereo e Doride, non muse.

---

## 2. File consegnabili (`~/Desktop/IBEC`)

| File | Cosa contiene |
|---|---|
| `NEREIDE.pdf` | Le 10 slide, inglese, 1440×810. La slide 10 mostra un fotogramma fisso del video |
| `NEREIDE.pptx` | Le stesse slide come immagini, con note del relatore in inglese, la GIF nella slide 9 e **il video completo nella slide 10** (8,7 MB) |
| Presentazione online | https://claude.ai/artifact/9V1pgqMUAGSeAbQM9yUYDd (privata, versione 39). La GIF si anima e il video parte da solo |
| `NEREIDE_tavole.pdf` | Fascicolo opzionale da 5 tavole A3 in inglese (consegna punto 4) |
| `NEREIDE_simulazione_ROS.mp4` | Video della simulazione montato: 56 s, 1280×752, con didascalie e dati |
| `NEREIDE_guida_presentazione.pdf` | Guida **in italiano**, 14 pagine: cosa dire per ogni slide, domande e risposte, appendice con le formule F1–F15 |
| `CAD/NEREIDE.solidcraft` | Modello CAD in crociera, nero e giallo |
| `CAD/NEREIDE_con_base.solidcraft`, `.step` | Velivolo in hovering agganciato alla docking station |
| `CAD/NEREIDE_scarico_campioni_e_batteria.gif` | Animazione della base, didascalie in inglese |

**Altro materiale nella cartella:**
- **Sorgenti video del collega:** `nereide_missione_1528.grezzo.mp4` (132 s, già a 2× tempo reale) e `nereide_missione_1528.mp4` (vecchio montaggio con scritte in italiano, non usato).
- **Da altri progetti, non toccare:** `VEDETTA*`, `ID.pdf`.
- **Vecchi file "NAIADE":** `CAD/NAIADE_*` e `CAD/2D/NAIADE_*` sono superati dai `NEREIDE_*`.

---

## 3. Le 10 slide

Ordine e nomi file in `NAIADE_slides/project/deck.json`. Sorgenti in `NAIADE_slides/project/slides/*.html`.

| # | File | Contenuto |
|---|---|---|
| 1 | `cover.html` | Titolo, frase sulle Nereidi, render CAD, riferimenti [1]–[4] |
| 2 | `missione.html` | 56% / 71% delle acque [2][3], tabella dei requisiti |
| 3 | `innovazione.html` | 4 novità e il riquadro INSPIRATION ("dal TiltOne solo l'architettura") |
| 4 | `concept.html` | Render in crociera e in hover, dati principali (3,06 m, 1,74 m, 25 kg, 8 × Ø 450, 108 km/h) |
| 5 | `propulsione.html` | Fasi di volo, "Why 8", incidenza variabile, scheda della portanza (259 N), apertura alare, pill del profilo |
| 6 | `struttura.html` | Vista da sotto con richiami 1–6: sensori fissi, moduli, batteria, pattini |
| 7 | `prelievo.html` | Analisi o prelievo, più **due righe piccole sulle soglie di batteria** |
| 8 | `energia.html` | Potenza per fase, energia della missione, 3 schede, formule |
| 9 | `dock.html` | Base solare: schema SVG A–F, GIF, 5 passi |
| 10 | `modello.html` | **Video ROS Gazebo** e colonna "How we built it" / "VS our sizing" |

**Modifiche recenti:**
- Ho tolto le pill dei criteri in alto a destra da tutte le slide.
- Ho tolto la scritta "moves in the presentation" (slide 9).
- Ho tolto la scritta "Video sped up 3–8×" sotto il video (slide 10): la velocità è già indicata dentro il video.
- Il modellino fisico è stato tolto: non fa parte della presentazione.

`NAIADE_slides/project/slides/` contiene anche 5 file vecchi non usati: `casi`, `problema`, `sensori`, `sostenibilita`, `video`. Non sono in `deck.json`.

---

## 4. Numeri di progetto (fonte unica: le slide)

| Grandezza | Valore |
|---|---|
| Massa, peso | 25 kg, W = 245 N |
| Ali | 2 × 3,0 × 0,28 m, NACA 2415, S = 1,68 m², AR 10,7, sfalsamento 710 mm |
| Apertura, lunghezza | 3,06 m, 1,74 m |
| Eliche | 8 × Ø 450 mm, area totale dei dischi 1,27 m² (carico sul disco 20 kg/m²) |
| Crociera | **30 m/s = 108 km/h**, C_L 0,28, L = 259 N (C_L strettamente necessario 0,26) |
| Stallo, Reynolds | ≈ 14 m/s (C_L max 1,3), Re ≈ 5,6·10⁵ |
| Incidenza variabile | α ≈ C_L/0,087 − 2,1°: 20 m/s → 4,7°, 25 → 2,3°, 30 → 1,1°, 35 → 0,1° |
| Potenze | hover 3,4 kW (FoM 0,8, η 0,8, v_i 8,9 m/s) · decollo 4,1 kW · crociera 0,66 kW (E 14) · installata ~7,5 kW (8 × 0,95) |
| Energia della missione | crociera 120 km = 0,73 kWh (67 min) + 4 prelievi 0,34 + decollo/atterraggio 0,07 = 1,14 su 1,5 kWh → resta 24% |
| Analisi, prelievo | 3 min = 0,17 kWh (11%) · 90 s = 0,085 kWh (6%) |
| Soglie di batteria | (0,30 + operazione + 0,0061·d + 0,035) / 1,5. A 10/30/50 km: analisi 38/46/54%, prelievo 32/40/49% |
| Base | ~2 × 1,5 m, pannello ~4 m² da 800 W di picco, 3 batterie a rotazione, scambio in meno di 2 min |

Tutti i calcoli passo per passo sono nella guida, appendice F1–F15.

---

## 5. Simulazione ROS Gazebo (lavoro del collega)

**Strumenti:** PX4 SITL + Gazebo Harmonic + ROS 2 Jazzy.
- Scheda del collega: `sim/PARAMETRI_SIMULAZIONE.md`.
- Volo di riferimento: `sim/logs/16_10_02.ulg`. Video aggiornato: `NEREIDE_simulation_ROS_v2.mp4` (già nella slide 10 di `TEAM_26.pptx`).
- `~/Downloads/Telegram Lite/sim.zip` è **troncato** (220,8 MB): mancano `sim/video/` e alcuni log. Il video è stato inviato a parte.

| Dato | Valore simulato | Nostro calcolo | Perché è diverso |
|---|---|---|---|
| Spinta/peso | 573 / 245 N = **2,3** (72 N per motore) | — | in hover usa il 43% della spinta |
| Hover | **3,7 kW**, ~18 min | 3,4 kW | FoM 0,7 contro 0,8; η 0,87 contro 0,8; carico non uniforme (baricentro avanzato) |
| Crociera **a 75 km/h** | **1,0 kW**, ~64 min, ~81 km | 0,46 kW alla stessa velocità | L/D 7,1 contro 14 (aerodinamica a piastra semplificata); η 0,70 contro 0,8 → la simulazione è il caso peggiore |
| Missione | base → lago 1 km → base in linea retta, 260 s simulati, atterraggio a meno di 10 cm dal centro con prua allineata, scena al Lago di Candia (mappa QGroundControl) | | |

**Le 2 correzioni al codice PX4** (`sim/px4_tiltwing.patch`):
1. `VT_BT_TW_KEEP`: nel ritorno in hover i motori e il controllo restano attivi mentre l'ala ruota. PX4 di serie li abbassa al minimo e il velivolo cadrebbe.
2. Saturazione dello yaw: con ali simmetriche lo yaw non va considerato saturato. Prima il velivolo girava su sé stesso.

**Incoerenze note:**
- La simulazione vola a **75 km/h** (crociera abbassata per virate e frenate più corte), le slide 4 e 5 dicono **108 km/h** di progetto. In slide 10 il confronto è fatto alla stessa velocità (0,46 kW).
- La scheda del collega cita "0,55 kW della slide 8": la slide 8 dice 0,66 kW (a 30 m/s). Va detto al collega.

**Montaggio del video** (`tools/video_sim_nereide.py`). Il grezzo è già a 2×. Le 7 fasi sono tagliate dal grezzo e accelerate:

| Fase | Tratto del grezzo | Velocità finale |
|---|---|---|
| 1 Decollo e transizione | 0–11 s | 3× |
| 2 Crociera | 11–30 s | 8× |
| 3 Frenata sul lago | 30–51 s | 6× |
| 4 Hover con la sonda | 51–71 s | 4× |
| 5 Rientro | 71–96 s | 6× |
| 6 Atterraggio | 96–122 s | 6× |
| 7 Base | 122–132 s | 4× |

Più una schermata finale di 5 s con la tabella dei dati. Stile delle scritte: barra nera con bordo giallo, riquadro dati in alto a sinistra, pill "N× SPEED · Video sped up" in alto a destra.

---

## 6. Come rigenerare tutto

**Ambiente Python** con pymupdf (fitz), PIL, python-pptx, imageio-ffmpeg, matplotlib, ezdxf. Sul Mac non c'è ffmpeg di sistema: si usa quello di `imageio_ffmpeg`.

**Slide → PDF, PPTX e guida (un comando):**
```
PY=<python con fitz e python-pptx> ~/Desktop/IBEC/tools/rebuild_deck.sh
```
Lo script fa questi passi:
1. HTML → `NEREIDE.pdf` con Chrome headless.
2. Rende le pagine in `tools/pptx/s01–s10.jpg` e le anteprime della guida.
3. Aggiorna le note PPTX dagli `<aside>` delle slide.
4. Genera `NEREIDE.pptx`, con GIF e video.
5. Genera `NEREIDE_guida_presentazione.pdf` da `tools/guida/guida.html`.

Controlla che le pagine siano 10.

**Presentazione online:** pubblicare con l'Artifact tool.
- `url` = il link sopra
- `root` = `~/Desktop/IBEC/NAIADE_slides`
- `file_path` = `.../project/deck.json`
- `files` = `{"project/slides/<nome>.html": "project/slides/<nome>.html"}` per ogni slide cambiata

**Tavole A3:**
```
cd ~/Desktop/IBEC && $PY -I tools/fascicolo_nereide.py CAD/2D/viste_dxf NEREIDE_tavole.pdf CAD/2D/NEREIDE CAD/2D/img
```

**Video:**
```
$PY -I tools/video_sim_nereide.py nereide_missione_1528.grezzo.mp4 NEREIDE_simulazione_ROS.mp4 <cartella_lavoro>
```
Poi rifare la copia leggera per la slide (960 px, crf 25), in `tools/video/embed.mp4`, e il fotogramma di copertina a 23 s, in `tools/video/poster.jpg`. Rimetterli come base64 in `modello.html`, nel tag `<video src=… poster=…>`.

**GIF della base:** `tools/gif/make_gif3.py <cartella_fotogrammi> <out.gif>`.
- Le didascalie sono nei dizionari `cc` e `bc`, la legenda in `leg`.
- I fotogrammi ricolorati erano nella cartella temporanea della sessione e **non sono stati salvati**. Per rifare la GIF servono di nuovo i render del CAD. Quella attuale va bene.
- La GIF è incorporata in base64 in `dock.html`.

**Note sulle slide:**
- Le immagini sono incorporate in base64 negli HTML: si modificano direttamente gli `.html` in `project/slides/`.
- Palette: nero #111111, giallo #F5C400, oro scuro #8F6B00 (testo su chiaro), carta #F5F4EF / #EAE8E0, grigi #5A5A55 / #BDBDB6, batterie arancio #E08A3C.
- I render stanno su pannelli chiari: un velivolo nero su fondo nero non si leggerebbe.

**SolidCraft (CAD):**
- Il server MCP scrive solo nella sua cartella temporanea.
- Assi: X = apertura, Y = avanti, Z = su.
- Il file aperto mantiene lo stato: dopo spostamenti per l'hover, ripristinare la crociera e salvare.
- Hover:
  - ala anteriore e A1–A4: trasla (0,−150,65), ruota 90° attorno a X, trasla (0,150,−65);
  - ala posteriore e P1–P4: stessa sequenza con (0,520,−290).

---

## 7. Cose da fare

1. **Rinominare il PDF finale in `26.pdf`** al momento della consegna.
2. Velocità di crociera: la simulazione resta a 75 km/h, spiegato in slide 10 con il confronto alla stessa velocità (fatto).
3. Scheda del collega aggiornata ai valori attuali (fatto).
4. Facoltativo: versione inglese dei testi "Cosa dire" della guida, se la presentazione è in inglese.
5. Facoltativo: chiedere di nuovo lo zip completo della simulazione, se servono i log mancanti.
6. Prima di consegnare, aprire `NEREIDE.pptx` in PowerPoint e verificare che il video parta (in PowerPoint il file era aperto durante le ultime generazioni: chiudere e riaprire).
