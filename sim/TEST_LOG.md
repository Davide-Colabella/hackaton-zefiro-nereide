# NAIADE: registro simulazioni (PX4 SITL + Gazebo Harmonic + ROS 2 Jazzy)

Data: 2026-11-14. I log di volo PX4 (.ulg) sono in `sim/logs/`, con l'orario UTC nel nome file.
Per analizzarli: `~/.venvs/cad/bin/python sim/analyze_log.py sim/logs/<file>.ulg`

## Toolchain
- PX4-Autopilot (main, clonato il 2026-11-14), SITL `make px4_sitl gz_<modello>`
- Gazebo Harmonic (gz sim 8.15), ROS 2 Jazzy, Micro-XRCE-DDS Agent 2.4.3, px4_msgs
- Bridge ROS 2 verificato: 73 topic `/fmu/*` (es. `/fmu/out/vehicle_status_v5`)

## Modello NAIADE (sim/naiade)
- Geometria da `CAD/NAIADE.step` (39 solidi), convertita con OpenCASCADE (`sim/export_meshes.py`)
- Configurazione: tandem box-wing, tilt-wing, 8 motori (4 per ala), eliche Ø450
- Ali basculanti: giunto 0° = hover, 90° = crociera; perni a x=+0.26 m (ala ant.) e x=-0.45 m (ala post.)
- Aerodinamica: LiftDrag per semiala (S = 0.42 m² ciascuna, NACA 2415, CLα = 4.75/rad), deriva fissa

### Parametri stimati e fonti
| Grandezza | Valore | Fonte |
|---|---|---|
| Batteria | 1.5 kWh → 6.0 kg | tav. 2 (1.5 kWh) + paper Tab. 10 (250 Wh/kg a livello pacco) |
| MTOW | 18 kg | stima: batteria circa 1/3 della massa (tipico per UAV elettrici); il paper dà 23% per un aerotaxi |
| Superficie alare | 1.68 m² (2 × 3.0 × 0.28) | tav. 1 |
| Carico alare | 10.7 kg/m² (105 N/m²) | calcolato |
| Area dischi | 8 × 0.159 = 1.27 m² → 14 kg/m² | tav. 1 (Ø450) |
| Spinta max/peso | 2.5 (55 N/motore) | scelta ≥ kT = 1.2 del paper (Tab./eq. 3) con margine per guasto motore |
| η elica | 0.8 | paper §2.4 |
| Accelerazione in transizione | 2 m/s² | paper §2.4 (ipotesi missione) |
| V crociera / stallo | ~18 / ~12 m/s | carico alare con CL 0.5 / CLmax 1.2 |
| Inerzie | Ixx 5.5, Iyy 2.4, Izz 7.5 kg m² (totali) | stima a masse concentrate |

## Test
| # | Log | Modello | Scopo | Esito |
|---|---|---|---|---|
| T01 | 11_23_21 | standard_vtol | prima prova della pipeline | il decollo non parte: senza GCS l'arming viene negato |
| T02 | 11_25_59 | standard_vtol | diagnosi | causa trovata: `NAV_DLL_ACT` richiede la GCS |
| T03 | 11_28_04 | standard_vtol | decollo e transizione con `NAV_DLL_ACT=0` | ok: 10 m, transizione FW, ~14 m/s |
| T04–T06 | 11_30_44, 11_32_07, 11_33_43 | standard_vtol | script `start_sim.sh` e bridge ROS 2 | ok: 73 topic ROS 2, l'agent si chiude correttamente |
| T07 | 11_57_13 | naiade v1 | primo volo | decolla a 15 m, instabile (pitch 44°), quad-chute; CA segnala imbardata insufficiente (KM 0.016) |
| T08 | 11_59_59 | naiade v1 + tuning live | GUI, `VT_FWD_THRUST_EN` 4→0, guadagni di rate abbassati | il tilt in hover causava cabrata; con guadagni bassi si ribalta |
| T09 | 12_06_49 | naiade v2 (Iyy ala 0.18, servo PD) | hover | oscillazione divergente in pitch, periodo ~2 s; il rate insegue il setpoint con ~0.4 s di ritardo |
| T10 | 12_08_35 | naiade v2 + guadagni rate ×2.7 | hover | nessun miglioramento: i parametri vecchi erano rimasti salvati, il reset non era avvenuto |
| T11 | 12_09_52 | naiade v2, reset parametri | hover 20 s | **hover stabile**: assetto ±0.5°, quota 15 m tenuta |
| T12 | 12_10_52 | naiade v2 | transizione | cabrata fino a 40°, poi quad-chute; i motori non generano coppia di pitch (bracci CA errati) |
| T13 | 12_13_41 | naiade v3 (`CA_ROTORi_PZ` alla quota del perno) | transizione | trim in hover 4.4°, oscillazione ±18° poi quad-chute |
| T14 | 12_15_25 | naiade v3 | verifica cinematica delle ali in volo | le ali ruotano (0.23→0.91 rad in 3 s); accelera verso est (vy) a ~3 m/s² fino a 10.7 m/s, poi **timeout di transizione** (CAS < 11 m/s dopo 6 s): con il tilt fermo a 54° l'ala è in stallo e frena |
| T15 | 12_33_40 | v3, `VT_TILT_TRANS` 0.85 (77°) | transizione | arriva a 11.7 m/s e si ferma lì, timeout dopo 16 s: a 77° c'è ancora troppa resistenza |
| T16 | 12_36_17 | v3, `VT_TILT_TRANS` 0.95, `VT_ARSP_TRANS` 12.5, 5× | transizione | **prima transizione completa** (FW a 7 s, 20–28 m/s), poi perde controllo di pitch e rollio in FW e precipita |
| T17 | 12_37_42 | v4: CG +6 cm in avanti, `FW_THR_TRIM` 0.2, 8× | transizione e crociera | FW raggiunto, ma rollio e pitch non seguono il setpoint (alettoni al 70% con effetto minimo) |
| T18 | (diagnostica live) | v4 | angolo dei giunti delle superfici in volo | alettone comandato a −0.42 rad, misurato −0.07 rad: il controllore di posizione è instabile su un giunto con inerzia 1e-6 e passo di 4 ms |
| T19 | 12_42_03 | v5: superfici con inerzia 2e-3, p 10, smorzamento 0.2, 8× | volo completo | ✅ **decollo, hover, transizione in 8 s, crociera stabile a 18.2 m/s**, quota 15 m ±1, motori al 24%, giro di attesa con rollio 23° |
| T20 | 12_43_36 | v5, GUI, tempo reale | ritorno in hover da crociera in virata | ❌ PX4 tiltrotor mette i motori al minimo e azzera il controllo MC mentre le ali ruotano (~1 s): l'ala perde portanza, il rollio passa da 25° a 95° e il drone si capovolge |
| T21 | 12_50_30 | v5 + patch PX4 `VT_BT_TW_KEEP=1`, `VT_BT_TILT_DUR 5`, `VT_B_DEC_MSS 1.5`, 8× | missione completa | ✅ **decollo → hover → transizione → crociera → ritorno in hover → atterraggio**; nel ritorno frena da 20 a 0 m/s in ~12 s, sale di 8 m durante la frenata e poi torna a 15 m; atterraggio `landed: True` |
| T22 | 12_52_26 | v6: colori CAD ed eliche rotanti (solo grafica, fisica identica), GUI, tempo reale | demo missione completa | ✅ decollo → transizione → crociera → ritorno in hover → atterraggio, `landed: True` |
| T23 | 13_01_13, 13_02_40 | v7: 25 kg e crociera 25 m/s (slide NEREIDE), verricello, carosello e batteria mobili | volo completo 8× | il primo fallisce (arming troppo presto: con 34 link del cavo il fattore reale scende a ~3.9×); il secondo, con attese sul fattore misurato, ✅ crociera a 25.2 m/s, quota ±0.3 m, atterraggio |
| T24 | 13_18_51 | missione MAVLink nel mondo NEREIDE | missione completa | transizioni ok; bug script: comandi del verricello via `gz topic` lenti e bloccanti, sonda calata in volo |
| T25 | 13_22_57 | missione, verricello non bloccante | missione completa | bug: waypoint della base inviato come lat/lon 0,0 → il drone si dirige verso il golfo di Guinea |
| T26 | 13_32_57 | missione corretta, modalità FAST (senza cavo, ~6×) | **missione NEREIDE completa** | ✅ decollo dalla base → FW a 54 s → hover sul lago a 10 m → sonda calata e risalita → FW → hover → atterraggio a **7 cm** dal centro della piattaforma → scarico campioni → cambio batteria; 330 s simulati in ~1 min reale |
| T27 | 13_34_34 | missione con cavo del verricello, GUI, tempo reale, stazionamento sul lago 90 s | **demo per il video** | ✅ missione completa in 325 s; la sonda risale prima della ripartenza; atterraggio a 7 cm dal centro; scarico campioni e cambio batteria |
| T28 | 13_45_44 | collisioni su vasche, edifici e alberi (54) e su fusoliera e ali; risalita a 30 m dopo il prelievo; rientro a sud, crociera a 40 m | missione FAST | ✅ `check_clearance.py`: ostacolo più vicino a 11.4 m, quota minima 18.8 m in transizione e 20 m in FW. Prima (T27) il rientro passava a 2.3 m dal fianco dell'edificio 1, sotto il livello del tetto |
| T29 | 13_48_09 | missione accorciata (giri stretti, sonda 10+10+10 s, stazionamento 42 s) | missione FAST | ✅ 251 s simulati (prima 325), ostacolo più vicino a 10.8 m, atterraggio a 8 cm dal centro |
| T30 | 13_54_57 | prima registrazione video (ffmpeg x11grab) | video | video di 49 s ok, ma: la camera perde il drone in crociera (follow pgain 0.01), cattura con i bordi della finestra, il drone ruota su sé stesso in hover |
| T31 | 14_01_01 | `MPC_YAW_MODE 5` (yaw fisso), `VT_B_DEC_MSS 2.5`, `NPFG_PERIOD 10`, giri più stretti | missione FAST | missione di 226 s, distanza massima 460 m (prima oltre 530), ostacolo più vicino a 9.3 m; **la rotazione resta**: 400° in 57 s sopra il lago |
| T32 | 14_02_53 | **patch PX4**: saturazione dello yaw in `ActuatorEffectivenessTiltrotorVTOL` | missione FAST | ✅ yaw fermo (±1° sul lago, 0° in atterraggio), `unallocated_torque z` = 0, atterraggio a 5 cm. Causa: senza tilt che controllano lo yaw PX4 segnalava lo yaw sempre saturato (+1) e il rate controller lo bloccava in un verso |

## Risultati volo T19 (`sim/report/12_42_03/`)
- Grafici: `flight.png` (quota, velocità, assetto, tilt con le fasi) e `power.png`; numeri in `summary.json`
- Hover: spinta 177 N (= peso), potenza stimata ~2.3 kW → autonomia in hover ~29 min (1.1 kWh utili)
- Transizione: 8.1 s, potenza media ~1.8 kW, picco di velocità 28 m/s, poi assestamento a 18 m/s
- Crociera: spinta 26 N → L/D ≈ 6.8; potenza ≈ T·V/(η_elica·η_motore·η_ESC) ≈ 680 W → **~98 min, ~107 km**
- Crociera e hover: la crociera consuma circa 3.4 volte meno, il che giustifica il tilt-wing per la missione di monitoraggio

## Parametri finali (sim/4050_gz_naiade)
MC: `MC_ROLLRATE_P/PITCHRATE_P 0.4`, `I 0.2`, `D 0.008`, `MC_ROLL_P/PITCH_P 4.5`, `VT_FWD_THRUST_EN 0`, `CA_ROTORi_KM ±0.05`
Transizione: `VT_TILT_TRANS 0.95`, `VT_F_TRANS_DUR 6`, `VT_F_TR_OL_TM 12`, `VT_ARSP_TRANS 12.5`, `VT_ARSP_BLEND 9`, `VT_TRANS_P2_DUR 2`
FW: `FW_AIRSPD_TRIM 18`, `FW_AIRSPD_MIN 14`, `FW_THR_TRIM 0.2`, `FW_P_LIM_MAX 20`

## Velocità della simulazione
`SPEED=8 sim/test_flight.sh 16 transition`: circa 40 s reali per 80 s simulati (`PX4_SIM_SPEED_FACTOR`).
Override dei parametri al volo: `PARAMS="NOME=valore ..."`.
In parallelo non si può: PX4 e Gazebo condividono porte e mondo, quindi si accelera invece di parallelizzare.

## Scoperte utili per il progetto
1. **Su un tilt-wing la spinta passa per il perno dell'ala**: il braccio di controllo in pitch è la distanza tra i perni (0.71 m), non tra le eliche.
2. **Durante la rotazione le eliche avanzano** di 0.38·sin(θ): il centro di spinta si sposta in avanti e genera un momento cabrante. Il CG va arretrato oppure il perno avvicinato al disco elica.
3. Con 8 eliche grandi l'autorità di imbardata in hover viene solo dalla coppia di reazione: servono eliche con passo/coppia adeguati, oppure il tilt differenziale delle due ali.
4. L'inerzia è alta (apertura 3 m) e l'autorità per unità di comando è bassa: i guadagni di rate PX4 vanno circa ×2.7 rispetto a un quadricottero (0.4 contro 0.15).
5. **Tilt-wing: l'incidenza dell'ala è 90° − tilt.** Sotto i ~77° di tilt l'ala è in stallo e frena: la transizione va fatta con il tilt quasi pieno (~85°) già in fase 1, sfruttando l'accelerazione.
7. **Ritorno in hover su tilt-wing:** non si possono spegnere i motori mentre l'ala ruota, come fa la logica PX4 pensata per i tiltrotor, perché i motori sono l'unica cosa che sostiene l'aereo quando l'ala smette di portare. Patch PX4: `VT_BT_TW_KEEP` (src/modules/vtol_att_control/tiltrotor.cpp) mantiene spinta e controllo e fa ruotare le ali in 5 s. La patch completa è in `sim/px4_tiltwing.patch`.
8. **Yaw su tilt-wing a ali simmetriche:** i tilt non possono comandare lo yaw, che deve venire dalla coppia differenziale delle eliche. PX4 però segnalava lo yaw come saturato e lo lasciava derivare; corretto in `ActuatorEffectivenessTiltrotorVTOL.cpp`.
6. Un CG avanzato di 6 cm (≈ 9% della distanza tra le ali) serve a dare margine statico in crociera al tandem.
