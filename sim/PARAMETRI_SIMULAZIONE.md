# NEREIDE: parametri e risultati della simulazione

Scheda per le slide. Strumenti: PX4 SITL + Gazebo Harmonic + ROS 2 Jazzy, 14/11/2026.
Volo di riferimento: `sim/logs/16_10_02.ulg`. Video: `NEREIDE_simulation_ROS_v2.mp4` (55 s, inglese, mappa QGroundControl). Dettaglio di tutti i 32+ test: `sim/TEST_LOG.md`.

## 1. Velivolo simulato

| Grandezza | Valore | Fonte |
|---|---|---|
| Configurazione | ala a scatola (box-wing) tandem, tilt-wing, 8 motori (4 per ala) | CAD |
| Apertura / lunghezza | 3.06 m / 1.74 m | tav. 1 |
| Ali | 2 × 3.0 m × corda 0.28 m, NACA 2415, sfalsamento 710 mm | tav. 1 |
| Superficie alare totale | 1.68 m² | calcolata |
| Eliche | 8 × Ø 450 mm, area dischi 1.27 m² | tav. 1 |
| MTOW | 25 kg | slide 4 |
| Carico alare | 14.9 kg/m² (146 N/m²) | calcolato |
| Carico sul disco | 19.7 kg/m² | calcolato |
| Batteria | 1.5 kWh, 250 Wh/kg → 6 kg | tav. 2 + paper, Tab. 10 |
| Inerzie (stima) | Ixx 6.8, Iyy 3.2, Izz 9.8 kg m² | masse concentrate |
| Perni delle ali | anteriore x +0.26 m, posteriore x −0.45 m | CAD |
| Baricentro | 6 cm avanti al punto medio tra le ali | scelto per la stabilità in crociera |

## 2. Propulsione (modello motore)

| Grandezza | Valore |
|---|---|
| Spinta | T = 1.12·10⁻⁴ · ω² [N] |
| Velocità max | 800 rad/s (7 640 rpm) → 72 N per motore |
| Spinta max totale / peso | 573 N / 245 N = **2.3** (il paper chiede almeno kT = 1.2) |
| Coppia di reazione | 0.05 × spinta (giro alternato orario/antiorario a coppie) |
| Comando motori in hover | anteriori ~77%, posteriori ~51% (CG avanzato) |

## 3. Aerodinamica (modello semplificato, non CFD)

| Grandezza | Valore |
|---|---|
| Portanza | CLα = 4.75 /rad, α₀ = +2°, stallo a 14° |
| Superfici di controllo | alettoni sull'ala anteriore, elevatore sull'ala posteriore (±0.5 rad) |
| Deriva | fissa, 0.08 m² |

## 4. Regolazioni PX4 principali (file `sim/4050_gz_naiade`)

| Area | Parametro | Valore | Perché |
|---|---|---|---|
| Hover | MC_ROLLRATE_P / MC_PITCHRATE_P | 0.5 | inerzia alta (3 m di apertura): circa 3 volte un quadricottero |
| Hover | MC_ROLL_P / MC_PITCH_P | 4.5 | |
| Hover | MPC_YAW_MODE | 5 (yaw fisso) | col default il drone ruotava su sé stesso sopra il waypoint |
| Transizione | VT_TILT_TRANS | 0.95 (85°) | sotto ~77° l'ala è in stallo (incidenza = 90° − tilt) |
| Transizione | VT_F_TRANS_DUR | 10 s | rotazione lenta: a 25 kg perdeva quota |
| Transizione | VT_ARSP_TRANS / BLEND | 15 / 11 m/s | |
| Ritorno in hover | VT_B_DEC_MSS | 3 m/s² | frenata in ~60 m |
| Ritorno in hover | VT_BT_TILT_DUR | 5 s | |
| Ala fissa | FW_AIRSPD_TRIM / MIN / MAX | 19 / 16 / 30 m/s | virate e frenate più corte (in volo misurati ~21 m/s = 75 km/h) |
| Ala fissa | FW_THR_TRIM | 0.3 | |

**Modifiche al codice PX4** (`sim/px4_tiltwing.patch`):
1. `VT_BT_TW_KEEP`: nel ritorno in hover la logica standard dei tiltrotor spegne i motori mentre le ali ruotano; su un tilt-wing l'ala perde portanza e il drone cade. La patch tiene motori e controllo attivi.
2. Saturazione dello yaw: con ali simmetriche i tilt non controllano lo yaw e PX4 lo segnalava sempre come saturato; il drone girava su sé stesso. Corretto.

## 5. Missione dimostrativa

Base solare (docking station) → lago a 1 km → base in linea retta. Durata 260 s simulati, video da 55 s. Scena collocata al Lago di Candia (TO) per la mappa.

| Fase | Cosa succede |
|---|---|
| Decollo | verticale fino a 20 m, ali verticali |
| Transizione | 10 s, poi crociera a ~75 km/h, quota 40 m, rotta dritta |
| Lago | frenata, hovering a 10 m, sonda calata di 9.6 m in ~10 s, 10 s in acqua, risalita in ~10 s |
| Rientro | risalita a 40 m, rotazione in hover verso la base, transizione, rotta dritta, frenata, rotazione sul posto per allinearsi |
| Base | atterraggio centrato (< 10 cm) con prua allineata alle guide, campioni nel frigo, cambio batteria |
| Sicurezza | ostacolo più vicino a > 9 m (script `sim/check_clearance.py`) |

## 6. Risultati energetici (dal volo simulato)

Potenza elettrica stimata da teoria impulsiva, con FoM 0.7, η motore 0.92, η ESC 0.95; batteria utile 1.5 kWh × 80% × 0.92 = 1.1 kWh.

| Fase | Spinta | Potenza | Autonomia |
|---|---|---|---|
| Hover | 245 N (= peso) | **~3.7 kW** | ~18 min solo in hover |
| Transizione | 175 N medi | ~2.7 kW | |
| Crociera ~21 m/s (75 km/h) | 34 N → L/D ≈ 7.1 | **~1.0 kW** (T·V / rendimenti) | ~64 min, ~81 km |

Confronto con il nostro dimensionamento alla stessa velocità (metodo della slide 8): hover 3.4 kW contro 3.7 kW simulati (FoM 0.8 contro 0.7); crociera a 75 km/h 0.46 kW (W·V/(E·η) con E = 14, η = 0.8) contro 1.0 kW simulati, perché l'aerodinamica del simulatore è semplificata (L/D 7.1 contro 14) e il rendimento propulsivo è 0.70 contro 0.8: **la simulazione è il caso conservativo**. Questi sono i valori in slide 10.

## 7. Cosa non è validato
- Masse, inerzie e coefficienti aerodinamici sono stime, non misure.
- Nessuna CFD: l'aerodinamica è un modello a lastra con stallo.
- La docking station in simulazione è semplificata (non il CAD definitivo).
- Il motore è potenziato rispetto alla prima stima (72 N invece di 55 N) per avere margine in transizione a 25 kg.
