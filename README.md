# ⛵ Reinforcement Learning Sailboat Simulation (v2)

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)
![RL](https://img.shields.io/badge/RL-Stable--Baselines3-green)

Dieses Repository enthält eine ROS2-basierte Simulationsumgebung für das Training autonomer Segelboote mittels Reinforcement Learning.

---

## 🛠 Voraussetzungen

Stelle sicher, dass die folgenden Pakete auf deinem System installiert sind:

* **ROS2 Humble**: Kommunikations-Middleware für die Nodes.
* **Stable Baselines3**: Framework für den PPO-Algorithmus.
* **Gymnasium**: Standard-Schnittstelle für RL-Umgebungen.
* **Pygame**: Rendering-Engine für die grafische Visualisierung.
* **NumPy**: Mathematische Berechnungen der Physik.

---

## 🚀 Installation & Build

Befolge diese Schritte, um das Projekt lokal einzurichten:

### 1. Repository klonen
```bash
cd ~/ros2_ws/src
git clone [https://github.com/Jan-Hueging/Reinforcement_Learning_Sailboat.git](https://github.com/Jan-Hueging/Reinforcement_Learning_Sailboat.git)