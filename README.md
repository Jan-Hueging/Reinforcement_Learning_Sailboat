# ⛵ Reinforcement Learning Sailboat Simulation (v2)

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)
![Python](https://img.shields.io/badge/Python-3.12+-yellow)
![RL](https://img.shields.io/badge/RL-Stable--Baselines3-green)

Dieses Repository umfasst eine ROS2-basierte Simulationsumgebung für das Training autonomer Segelboote mittels Reinforcement Learning.

---

## 🛠 Voraussetzungen

Die folgenden Systemkomponenten werden für den Betrieb zwingend vorausgesetzt:

* **ROS2 Jazzy**: Kommunikations-Middleware für die Nodes.
* **Python 3.12+**: Primäre Programmiersprache der Umgebung.
* **Stable Baselines3**: Framework zur Ausführung des PPO-Algorithmus.
* **Gymnasium**: Standardisierte Schnittstelle für RL-Umgebungen.
* **Pygame**: Rendering-Engine für die grafische Visualisierung.
* **NumPy**: Bibliothek für mathematische Berechnungen der Physik.

---

## 🚀 Installation & Build

Übersicht der notwendigen Schritte zur Erstellung des Workspaces und zur Installation der definierten Abhängigkeiten:

### 1. Repository klonen
```bash
cd ~/ros2_ws/src
git clone [https://github.com/Jan-Hueging/Reinforcement_Learning_Sailboat.git](https://github.com/Jan-Hueging/Reinforcement_Learning_Sailboat.git)
```

### 2. Abhängigkeiten installieren
Die benötigten Python-Bibliotheken sind in der Datei `requirements.txt` hinterlegt und werden darüber installiert:
```bash
cd ~/ros2_ws/src/dummy_sailboat_sim
pip install -r requirements.txt
```

### 3. Workspace kompilieren
```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select dummy_sailboat_sim
source install/setup.bash
```

---

## 🧠 Training starten

Für den Lernprozess ist der parallele Betrieb von Simulation und Trainingsskript erforderlich.

1. **Physik-Simulation starten:**
   ```bash
   ros2 run dummy_sailboat_sim dummy_node
   ```

2. **Radar-Visualisierung öffnen (optional):**
   ```bash
   ros2 run dummy_sailboat_sim visualizer_node --ros-args --log-level WARN
   ```

3. **KI-Lernprozess starten:**
   ```bash
   python3 src/dummy_sailboat_sim/dummy_sailboat_sim/train.py
   ```

---

## 📡 ROS2 Topics (Bridge Architektur)

Die Simulation und die KI sind durch eine saubere **Bridge-Architektur** (`sailboat_gym_env.py`) getrennt. Die Kommunikation erfolgt ausschließlich über standardisierte ROS2-Topics. So kann das trainierte Modell später ohne Code-Änderungen vom Dummy direkt auf das echte Boot übertragen werden!

### 📥 Inputs (Sensorik vom Boot ➔ KI)
| Topic | ROS Message Typ | Beschreibung |
| :--- | :--- | :--- |
| `/GPS` | `geometry_msgs/Point` | Globale Position des Bootes (die Bridge errechnet daraus die Vorwärtsgeschwindigkeit und Distanz) |
| `/Kompass` | `std_msgs/Float64` | Globale Ausrichtung (Heading) des Bootes (daraus errechnet die Bridge die Drehgeschwindigkeit) |
| `/Neigung` | `std_msgs/Float64` | Krängung (Kippen des Bootes) |
| `/Windgeschwindigkeit` | `std_msgs/Float64` | Gemessener scheinbarer Wind |
| `/Windrichtung` | `std_msgs/Float64` | Relativer Winkel des scheinbaren Windes |
| `/Ruderstellung_Ist` | `std_msgs/Float64` | Aktueller Winkel des Ruders |
| `/Segelstellung_Ist` | `std_msgs/Float64` | Aktueller Winkel des Segels |

### 📤 Outputs (KI ➔ Steuerung des Bootes)
| Topic | ROS Message Typ | Beschreibung |
| :--- | :--- | :--- |
| `/Ruderstellung_Soll` | `std_msgs/Float64` | Gewünschter Zielwinkel für das Ruder (ausgegeben als relative Änderung / Delta) |
| `/Segelstellung_Soll` | `std_msgs/Float64` | Gewünschter Zielwinkel für das Segel (ausgegeben als relative Änderung / Delta) |

---

## 📂 Projektstruktur

| Datei / Ordner | Kurzbeschreibung |
| :--- | :--- |
| `config.py` | Zentrale Definitionsdatei für alle Physik- und Trainingsparameter. |
| `dummy_node.py` | Berechnung der Bootsphysik und Verarbeitung von Steuerbefehlen. |
| `reward_calculator.py` | Ausgelagerte Belohnungsfunktion (Reward-Logik) für das Neuronale Netz. |
| `sailboat_gym_env.py` | Definition des Beobachtungsraums (Bridge) und Schnittstelle zur KI. |
| `train.py` | Initialisierung des Modells und Ausführung der Trainingsschleife. |
| `visualizer_node.py` | Grafische Echtzeit-Darstellung von Boot, Wind und Ziel. |
| `requirements.txt` | Liste aller erforderlichen Python-Bibliotheken und Versionen. |
| `models/` | Automatischer Speicherort für fertig trainierte KI-Modelle. |

---

## ⚙️ Wichtige Konzepte

* **Delta-Control**: Die KI erlernt schrittweise Korrekturen anstatt absoluter Winkel.
* **Domain Randomization**: Der Zielpunkt wechselt nach jedem Reset zufällig die Position.
* **Action Smoothing**: Strafen für abrupte Bewegungen fördern ein ruhiges Segelverhalten.
* **Reset-Service**: Eine automatische Rücksetzung teleportiert das Boot bei Episodenende zum Start.

---

## 📊 Monitoring

Relevante Metriken zur Überwachung des Trainingsfortschritts im Terminal:

* **ep_rew_mean**: Durchschnittliche Belohnung pro Lauf (Wachstum erwartet).
* **fps**: Ausführungsgeschwindigkeit der Simulation (Indikator für Performance).
* **std**: Streuung der gewählten Aktionen (Reduktion bei zunehmender Sicherheit der KI).

---
*Entwickelt für die Forschung im Bereich autonomes Segeln mit ROS2 und Reinforcement Learning.*