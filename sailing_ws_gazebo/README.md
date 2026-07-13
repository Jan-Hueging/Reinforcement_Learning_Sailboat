# Gazebo Sailing Workspace (`sailing_ws_gazebo`)

Dieses Repository / dieser Workspace enthält die offizielle 3D-Physiksimulation der Simulationsgruppe, basierend auf ROS 2 und Gazebo Harmonic (inkl. VRX).

## 🛠️ Systemvoraussetzungen (Prerequisites)

Um den Workspace kompilieren und ausführen zu können, müssen folgende Komponenten auf dem Host-System installiert sein:
1. **ROS 2 Jazzy** (Desktop Full)
2. **Gazebo Harmonic** (Version 8)
   - Konkret benötigt werden die Bibliotheken `gz-sim8` und `gz-transport13`.
3. **ROS-Gazebo-Bridges**
   - Paket: `ros-jazzy-ros-gz`

## 📦 Kompilieren (Installation)

Da es sich um einen klassischen ROS 2 Workspace handelt, wird er mit `colcon` kompiliert. **Wichtig:** Dieser Workspace wird *unabhängig* vom KI-Docker-Container auf dem Host-Rechner (oder in einem eigenen Docker) gebaut und gestartet.

1. Terminal im Hauptverzeichnis `sailing_ws_gazebo` öffnen.
2. ROS 2 Umgebung laden:
   ```bash
   source /opt/ros/jazzy/setup.bash
   ```
3. Den kompletten Workspace kompilieren:
   ```bash
   colcon build --symlink-install
   ```

## 📂 Struktur der Pakete

* **`opti_controller`**
  Enthält die Launch-Dateien (z.B. `vrx_testwelt.launch.py`) und den Python-Knoten `sensor_transformer.py`, der die Sensordaten des Bootes aufbereitet.
* **`sailing_plugins`**
  Die Kern-Physik! In C++ geschriebene Plugins für Gazebo Harmonic. Insbesondere das `SailLimitPlugin`, welches die physischen Beschränkungen der Segelschot durchsetzt und auf Transport-Ebene direkt mit Gazebo kommuniziert.
* **`vrx`**
  Der Fork der maritimen Simulation (Virtual RobotX). Sorgt für Wellengang, Auftrieb, Wasser-Rendering und Wind-Modelle.

## 🚀 Simulation starten

Nach dem erfolgreichen Build muss die Umgebung geladen werden, bevor die Welt gestartet werden kann:

```bash
source install/setup.bash
ros2 launch opti_controller vrx_testwelt.launch.py
```

> **Bekannte Limitierung im `sensor_transformer.py`:**
> Der Python-Knoten lauscht aktuell hartcodiert auf das Topic `/world/sydney_regatta/model/opti_boot/joint_state`. Wenn über die Launch-File stattdessen die *Testwelt* (`test_world`) gestartet wird, kommen die Ruder- und Segelstellungen nicht im ROS 2 System an. Der Name muss im Python-Skript angepasst werden!
> Zudem ist die Wind-Brücke in der Datei `boot.launch.py` aktuell auskommentiert.

## 🤖 Verbindung zum KI-Training (Reinforcement Learning)

Die Simulationsgruppe und die KI-Gruppe sind dank ROS 2 vollständig voneinander **entkoppelt**.

**So funktioniert das Zusammenspiel:**
1. Startet diese Gazebo-Simulation (`sailing_ws_gazebo`) ganz normal auf dem PC.
2. Sobald Gazebo läuft, wird automatisch die Simulationszeit auf dem Topic `/clock` publiziert.
3. Die KI-Gruppe startet ihr Training im Docker (`sudo make run-training`).
4. **Die Magie:** Der KI-Docker-Container klinkt sich über das Netzwerk (ROS_DOMAIN_ID=42) ein. Die KI wartet automatisch auf den Tick der Gazebo-Uhr (`use_sim_time=True`). Gleichzeitig startet der KI-Container unsichtbar eine eigene Bridge, die alle `/Segelstellung_Soll` und `/Ruderstellung_Soll` ROS-Befehle direkt an das Gazebo `SailLimitPlugin` eurer Simulationsgruppe weiterleitet.

Zusammengefasst: Es sind keinerlei Anpassungen an diesem Workspace nötig, um die KI anzudocken!
