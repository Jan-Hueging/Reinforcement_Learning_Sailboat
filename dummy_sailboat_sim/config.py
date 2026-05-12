# config.py
import math

class Config:

    # ===============================================
    # ⚙️ 1. Physik-Parameter (Dummy-Boot)
    # ==========================================

    # ⚠️ nicht innerhalb eines Trainings verändern!
    MAX_RUDDER_ANGLE = 0.785        # [rad]     Max. Ruderwinkel
    MAX_SAIL_ANGLE = math.pi        # [rad]     Max. Segelwinkel
    MAX_RUDDER_DELTA = 0.05         # [rad]     Max. Ruderdelta pro Step
    MAX_SAIL_DELTA = 0.05           # [rad]     Max. Segeldelta pro Step
    
    DUMMY_RUDDER_EFFECT = 0.5       # [/]       Rudereffekt
    DUMMY_SAIL_EFFICIENCY = 0.3     # [0-1]     Max. Segeleffizienz
    DUMMY_INERTIA = 0.1             # [0-1]     Trägheit (pro Step)
    DUMMY_HEEL_STIFFNESS = 0.1      # [rad*s/m] Krängungsfaktor

    TARGET_REWARD_RADIUS = 5.0      # [Meter]   Größe des Ziels
    OUT_OF_BOUNDS_RADIUS = 150.0    # [Meter]   Out of Bounds
    TARGET_SPAWN_X = (20.0, 75.0)  # [Meter]   Zielbereich X
    TARGET_SPAWN_Y = (-50.0, 50.0)  # [Meter]   Zielbereich Y

    WIND_SPEED_DEFAULT = 5.0        # [m/s]     konst. Windgeschwindigkeit
    WIND_ANGLE_DEFAULT = math.pi    # [rad]     konst. Windrichtung

    # ===============================================
    # 🏁 2. Start-Zustände
    # ==========================================
    
    START_X = 0.0                   # [Meter]   Startposition X
    START_Y = 0.0                   # [Meter]   Startposition Y
    START_THETA = 0.0               # [rad]     Startausrichtung
    START_V = 0.0                   # [m/s]     Startgeschwindigkeit
    INITIAL_RUDDER_ANGLE = 0.0      # [rad]     Start-Ruderwinkel
    INITIAL_SAIL_ANGLE = math.pi/2  # [rad]     Start-Segelwinkel


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
    MAX_EPISODE_STEPS = 1024        # [Steps]   Abbruchspunkt 
    

    # ===============================================
    # 💰 5. Belohnungssystem
    # ==========================================

    REWARD_SUCCESS = 20.0           # [/]       Belohnung - Ziel erreicht
    REWARD_FAIL = -10.0             # [/]       Strafe    - Rausgefahren
    REWARD_TIME_PENALTY = -0.01     # [/]       Strafe    - Zeitdruck    
    PENALTY_ACTION_JITTER = -0.05   # [/]       Strafe    - Zucken


    # ===============================================
    # 📁 6. DATEIEN & VERSIONIERUNG
    # ==========================================

    # Name des zu trainierenden Modells
    MODEL_NAME = "sailboat_model_v2"

