# Projekt- und Übergabebericht: Autonomes Segeln mit Reinforcement Learning

Dieses Dokument dient als roter Faden und Strukturvorlage für den Abschlussbericht (ca. 15 Seiten).
---

## 1. Einleitung & Motivation
*(Den gewählten Ansatz begründen)*

- **Problemstellung:** Ein Segelboot autonom steuern zu lassen, ist sehr komplex. Windgeschwindigkeiten, Wellen und Abdrift sind schwer vorhersehbare; nicht-lineare Störgrößen.
- **Reinforcement Learning:** Anstatt einen klassischen, starren PID-Regler zu programmieren, der für jede Situation eine feste Regel braucht, nutzen wir Machine Learning (Programmierung eines "digitalen Steuermannes" (Agent), der das Segeln in einer Simulation durch Ausprobieren selbst lernt).
- **Projektziel:** Entwicklung einer robusten KI-Steuerung, die ein Segelboot sicher und schnell zu einer Zielkoordinate navigiert, ohne zu kentern.

---

## 2. Systemarchitektur: Das Zusammenspiel der Komponenten
*(Setup erklären)*

- **Modularer Ansatz:** Intelligenz ist strikt von der Physik getrennt. Eine Gruppe baut die Simulation, die andere das Training.
- **Kommunikation via ROS2:** Architektur ist über Topics verbunden. Boot sendet Sensordaten (`/GPS`, `/Windrichtung`, `/Neigung`), die KI sendet Steuerbefehle (`/Ruderstellung_Soll`, `/Segelstellung_Soll`) zurück.
- **KI-Frameworks:** Nutzung von `Stable Baselines3` für den  PPO-Algorithmus und `Gymnasium` als Umgebung, die die ROS2-Kommunikation für die KI übersetzt.
- 🖼️ **Visualisierung:** Blockschaltbild rein! Zeichnung mit Pfeilen zwischen "Physik-Node", "Gymnasium Wrapper" und "PPO Agent".

---

## 3. Die Schnittstellen der KI
*(Wie nimmt die KI die Welt wahr und wie greift sie ein?)*

### Observation Space
- Welche Daten bekommt die KI? Keine Rohdaten, sondern Aufbereitung von Zuständen: Distanz zum Ziel, relativer Winkel zum Ziel, Neigung (Krängung), sowie Windgeschwindigkeit und -richtung.
- **Wichtig:** Erklärung der Normierung. KI bekommt Werte zwischen -1 und 1. (Z.B. wird die Distanz in einen Prozentwert der Maximaldistanz umgerechnet).
- 💻 *Code:* Kurzer Auszug aus `_get_obs()` aus der `sailboat_gym_env.py`.

### Action Space
- Wie steuert die KI? Erklärung der **Delta-Steuerung**. KI setzt nicht den absoluten Winkel, sondern bestimmt die Änderungsrate.
- Segel wird hierbei als Großschot (Begrenzung des Ausstellwinkels) verstanden.

---

## 4. Die Reward-Funktion

- **Einleitung:** Mathematisches Definieren, was "gutes Segeln" ist.
- **Velocity Made Good:** Distanz allein reicht nicht (verleitet dazu, im Kreis zu fahren) → Belohnung für *effektive Geschwindigkeit* in Richtung des Ziels.
  - 🖼️ *Visualisierung:* Diagramm → Segelboot, dessen Geschwindigkeitsvektor in VMG und Quer-Geschwindigkeit zerlegt ist.
- **Jitter-Penalty:** "ruckartige" Lenkmanöver werden bestraft (`abs(delta_rudder) + abs(delta_sail)`). Schont das Material und verhindert Strömungsabrisse.
- **Kenter-Schutz:** *Exponentielle* Krängungsstrafe (`heel_angle ** 2`). Boot darf sich leicht neigen, um Fahrt aufzunehmen, wird aber kurz vor dem Kentern massiv bestraft.
- **Time Penalty & Workspace:** KI bekommt stetig Minuspunkte für die verstrichene Zeit → Vermeidet Trödeln. Festes Arbeitsfeld (Bounding Box), um das Training zu stabilisieren.
- 💻 *Code:* Inhalt der `calculate()` Funktion aus `reward_calculator.py`.

---

## 5. Trainingsablauf und Evaluation
*(Wie wurde trainiert? Wie gut funktioniert es?)*

- **Trainingsloop:** Was passiert in einer Episode? (Reset, Segeln, Abbruch bei Erfolg oder Verlassen der Box).
- **Hyperparameter:** Blick in die `config.py`.
- 📈 **Graphen:** Screenshots aus dem TensorBoard.
  - *Graph 1: Mean Reward.* Zeigt, wie die KI im Laufe der Millionen Schritte immer mehr Belohnung einsammelt.
  - *Graph 2: Episode Length.* Zeigt, ob die KI das Ziel immer schneller erreicht.

---

## 6. Zusammenfassung, Limitierungen und Ausblick
*(Abschluss und Übergabe an die nächste Gruppe)*

- **Erreichte Ziele:** Was funktioniert?
- **Limitierungen:** Was sind die Schwierigkeiten bei Segel-KI?. KI kann noch nicht kreuzen (sie wird dafür nicht belohnt)
- **Nächste Schritte:**
  1. **In-Irons-Penalty implementieren:** Strafe hinzufügen, wenn das Boot gegen den Wind steht und zu langsam wird, um es zum Kreuzen zu zwingen.
  2. **Fine-Tuning:** Anpassung der Parameter in `config.py` an das finale Physik-Modell.

---
