# ⛵ Reinforcement Learning Sailboat Simulation (v2)

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)
![Python](https://img.shields.io/badge/Python-3.12+-yellow)
![RL](https://img.shields.io/badge/RL-Stable--Baselines3-green)

Dieses Repository umfasst eine ROS2-basierte Simulationsumgebung für das Training autonomer Segelboote mittels Reinforcement Learning.

---

## 🛠 Voraussetzungen

Je nachdem, für welchen Weg du dich entscheidest, brauchst du unterschiedliche Programme:

**Für das empfohlene Docker-Setup:**
* **Docker** & **Docker Compose**
* **Git** (um das Repository herunterzuladen)
* Ein **Linux-System** (für die grafische X11-Weiterleitung)

**Für die manuelle, lokale Installation (ohne Docker):**
* **ROS2 Jazzy**: Kommunikations-Middleware für die Nodes.
* **Python 3.12+**: Primäre Programmiersprache der Umgebung.
* **Stable Baselines3**: Framework zur Ausführung des PPO-Algorithmus.
* **Gymnasium**: Standardisierte Schnittstelle für RL-Umgebungen.
* **Pygame**: Rendering-Engine für die grafische Visualisierung.
* **NumPy**: Bibliothek für mathematische Berechnungen der Physik.

---

## 🐳 Docker Setup (Empfohlen: Einfachster Weg)

Wenn du ohne Vorwissen direkt starten möchtest, nutze unsere vorbereitete Docker-Umgebung. Docker lädt alle nötigen Programme (ROS2, Python, etc.) automatisch herunter und richtet sie ein.

### 1. Vorbereitung & Installation
Öffne ein Terminal auf deinem PC und lade dir zuerst dieses Repository (welches die Docker-Konfiguration enthält) herunter. Anschließend navigierst du in den `docker` Ordner und startest das Setup:

```bash
git clone https://github.com/Jan-Hueging/Reinforcement_Learning_Sailboat.git
cd Reinforcement_Learning_Sailboat/docker
sudo make setup
```

### 2. Simulation & Training starten
Sobald das Setup abgeschlossen ist, kannst du die komplette Umgebung (Simulation, Radar-Visualisierung und KI-Training) mit einem einzigen Befehl starten:

```bash
sudo make run-all
```

*(Zum Beenden einfach `Strg+C` drücken).*

**Möchtest du die Komponenten einzeln starten?** Öffne dafür jeweils ein neues Terminal im `docker` Ordner:
* **Physik-Simulation:** `sudo make run-physics`
* **Visualisierung:** `sudo make run-visualizer`
* **KI-Training:** `sudo make run-training`

---

## 🚀 Lokale Installation (Alternativ ohne Docker)

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

## 🧠 Training starten (Lokale Installation)

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

## 📂 Projektstruktur

| Datei / Ordner | Kurzbeschreibung |
| :--- | :--- |
| `config.py` | Zentrale Definitionsdatei für alle Physik- und Trainingsparameter. |
| `dummy_node.py` | Berechnung der Bootsphysik und Verarbeitung von Steuerbefehlen. |
| `sailboat_gym_env.py` | Definition des Beobachtungsraums und der Belohnungsfunktion. |
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