# config.py
import math

class Config:

    # ===============================================
    # ⚙️ 1. Physik-Parameter (Dummy-Boot)
    # ==========================================

    # ⚠️ nicht innerhalb eines Trainings verändern!
    MAX_RUDDER_ANGLE_DEG = 45.0     # [Grad]    Max. Ruderwinkel
    MAX_SAIL_ANGLE_DEG = 70.0       # [Grad]    Max. Segelwinkel
    MAX_RUDDER_DELTA_NORM = 0.05    # [/]       Normiertes Ruderdelta pro Step (-1 bis 1)
    MAX_SAIL_DELTA_NORM = 0.05      # [/]       Normiertes Segeldelta pro Step (-1 bis 1)
    
    DUMMY_RUDDER_EFFECT = 0.5       # [/]       Rudereffekt
    DUMMY_SAIL_EFFICIENCY = 0.3     # [0-1]     Max. Segeleffizienz
    DUMMY_INERTIA = 0.1             # [0-1]     Trägheit (pro Step)
    DUMMY_HEEL_STIFFNESS = 0.1      # [rad*s/m] Krängungsfaktor

    TARGET_REWARD_RADIUS = 5.0      # [Meter]   Größe des Ziels
    WORKSPACE_X_MIN = -100.0        # [Meter]   Linke Grenze des Arbeitsfeldes
    WORKSPACE_X_MAX = 100.0         # [Meter]   Rechte Grenze des Arbeitsfeldes
    WORKSPACE_Y_MIN = -100.0        # [Meter]   Untere Grenze des Arbeitsfeldes
    WORKSPACE_Y_MAX = 100.0         # [Meter]   Obere Grenze des Arbeitsfeldes
    
    TARGET_SPAWN_X = (10.0, 80.0)   # [Meter]   Zielbereich X (gesamte Sichtfläche vor dem Boot)
    TARGET_SPAWN_Y = (-30.0, 30.0)  # [Meter]   Zielbereich Y (gesamte Sichtfläche)

    WIND_SPEED_DEFAULT = 5.0        # [m/s]     konst. Windgeschwindigkeit
    WIND_ANGLE_DEFAULT = 0.0        # [rad]     konst. Windrichtung (Rückenwind)

    # ===============================================
    # 🏁 2. Start-Zustände
    # ==========================================
    
    START_X = 0.0                   # [Meter]   Startposition X
    START_Y = 0.0                   # [Meter]   Startposition Y
    START_THETA = 0.0               # [rad]     Startausrichtung
    START_V = 0.0                   # [m/s]     Startgeschwindigkeit
    INITIAL_RUDDER_ANGLE_DEG = 0.0  # [Grad]    Start-Ruderwinkel
    INITIAL_SAIL_ANGLE_DEG = 35.0   # [Grad]    Start-Segelwinkel


    # ===============================================
    # 🧠 3. Trainingsrahmen
    # ==========================================

    TOTAL_TIMESTEPS = 1000000       # [Steps]   Gesamtdauer
    N_STEPS = 2048                  # [Steps]   pro Iteration
    LEARNING_RATE = 0.0003          # [/]       Lerngeschwindigkeit
    

    # ===============================================
    # ⏱️ 4. Taktung
    # ==========================================

    STEP_TIME_SEC = 0.025           # [Sekunde] Schrittgeschwindigkeit   
    MAX_EPISODE_STEPS = 3072        # [Steps]   Abbruchspunkt 
    

    # ===============================================
    # 💰 5. Belohnungssystem
    # ==========================================

    REWARD_VMG_MULTIPLIER = 10.0    # [/]       Belohnung - VMG (Velocity Made Good) Multiplikator
    REWARD_SUCCESS = 20.0           # [/]       Belohnung - Ziel erreicht
    REWARD_FAIL = -10.0             # [/]       Strafe    - Rausgefahren
    REWARD_TIME_PENALTY = -0.01     # [/]       Strafe    - Zeitdruck    
    PENALTY_ACTION_JITTER = -0.05   # [/]       Strafe    - Zucken
    PENALTY_HEEL = -1.0             # [/]       Strafe    - Krängung (wird mit Winkel^2 multipliziert)


    # ===============================================
    # 📁 6. DATEIEN & VERSIONIERUNG
    # ==========================================

    # Name des zu trainierenden Modells
    MODEL_NAME = "sailboat_model_v2"


    # ===============================================
    # 📡 7. ROS TOPICS
    # ==========================================

    TOPIC_GPS = '/GPS'
    TOPIC_COMPASS = '/Kompass'
    TOPIC_HEEL = '/Neigung'
    TOPIC_RUDDER_IST = '/Ruderstellung_Ist'
    TOPIC_RUDDER_SOLL = '/Ruderstellung_Soll_Autonom'
    TOPIC_SAIL_IST = '/Segelstellung_Ist'
    TOPIC_SAIL_SOLL = '/Segelstellung_Soll_Autonom'
    TOPIC_WIND_SPEED = '/Windgeschwindigkeit'
    TOPIC_WIND_DIR = '/Windrichtung'
