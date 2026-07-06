# 🗺️ Roadmap: Entwicklung der Segelboot-Belohnungsfunktion

Dieses Dokument dient als zentraler Ablaufplan für die Entwicklung und Optimierung der Belohnungsfunktion (Reward Function) unseres Reinforcement Learning Agenten.

Wir entwickeln die Funktion iterativ in 3 Stufen, um sicherzustellen, dass die KI sauberes Segeln lernt und nicht durch zu viele gleichzeitige Regeln verwirrt wird.

---

## ✅ Stufe 1: Basic Navigation (VMG & Terminal Rewards) - **ABGESCHLOSSEN**
**Ziel:** Das Boot soll lernen, sich überhaupt in Richtung des Ziels zu bewegen, auch wenn es gegen den Wind kreuzen muss.

### Mathematischer Ansatz: VMG (Velocity Made Good)
Anstatt nur die absolute Distanz zu belohnen, belohnen wir die **effektive Geschwindigkeit auf das Ziel zu**.
`VMG = Vorwärtsgeschwindigkeit * cos(Winkel_zum_Ziel)`
- Fährt das Boot direkt aufs Ziel zu: VMG = 100% der Geschwindigkeit (Maximaler Reward).
- Fährt das Boot quer zum Ziel: VMG = 0 (Kein Reward).
- Fährt das Boot vom Ziel weg: VMG ist negativ (Strafe).

### ToDos Stufe 1
- [x] Signatur der `calculate()` Funktion in `reward_calculator.py` anpassen, sodass sie nicht nur Distanzen, sondern auch `v_linear` und `angle_to_target` empfängt.
- [x] VMG-Formel implementieren und als primären dichten Reward ausgeben.
- [x] Terminal Rewards anpassen (+100 für Ziel, -50 für Out of Bounds).

---

## ⚙️ Stufe 2: Action Smoothing & Zeitdruck
**Ziel:** Das Boot soll aufhören, wild mit den Segeln und Rudern zu zucken, und lernen, effiziente, weiche Manöver zu fahren.

### Mathematischer Ansatz
- **Jitter-Penalty:** `-w * (abs(delta_rudder) + abs(delta_sail))`
- **Zeit-Penalty:** Konstante kleine Strafe pro Zeitschritt (z.B. `-0.01`), damit das Boot motiviert ist, VMG zu maximieren und nicht zu trödeln.

### ToDos Stufe 2
- [x] Jitter-Penalty anhand der ausgeführten `action` Arrays implementieren.
- [x] Zeitstrafe kalibrieren, damit sie nicht den VMG-Reward überlagert.

---

## 🛡️ Stufe 3: Kenter-Schutz & No-Go-Zone (Safety)
**Ziel:** Das Boot soll physikalische Grenzen respektieren (nicht umkippen, nicht im Wind stehen bleiben).

### Mathematischer Ansatz
- **Heel-Penalty:** Strafe, wenn die Krängung (`heel_angle`) einen kritischen Wert überschreitet. Steigt exponentiell an.
- **In-Irons-Penalty:** Strafe, wenn das Boot zu langsam ist UND direkt im Wind steht.

### ToDos Stufe 3
- [x] `heel_angle` als Parameter an die Reward-Funktion übergeben.
- [ ] Exponentielle Strafenfunktion für Krängung implementieren.
- [ ] Parameter (Gewichtungen) so tunen, dass das Boot rechtzeitig das Segel öffnet (auffiert), um nicht zu kentern.

---
*Letztes Update: Stufe 1 erfolgreich abgeschlossen*
