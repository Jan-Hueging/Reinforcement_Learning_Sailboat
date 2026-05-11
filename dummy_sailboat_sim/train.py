import rclpy
from stable_baselines3 import PPO
from sailboat_gym_env import SailboatEnv # Importiert deine Umgebung

def main():
    print("🧠 Initialisiere KI-Training...")
    
    # 1. ROS2 im Hintergrund starten (wichtig für die Kommunikation)
    rclpy.init()
    
    # 2. Die Umgebung (das Rückenmark) erschaffen
    env = SailboatEnv()
    
    # 3. Das Gehirn (PPO Algorithmus) erschaffen
    # "MlpPolicy" sagt der KI: Nutze ein Standard Neural Network
    # verbose=1 sagt der KI: Gib uns Status-Updates im Terminal
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003, n_steps=2048)
    
    print("🚀 Training startet jetzt! Beobachte das Radar-Fenster.")
    
    try:
        # 4. Der eigentliche Trainings-Prozess
        # 20.000 Schritte sind ein guter erster Test-Lauf (dauert ein paar Minuten)
        model.learn(total_timesteps=20000)
        
        # 5. Gehirn speichern, wenn es fertig ist
        model.save("sailboat_model_v1")
        print("✅ Training beendet! Modell wurde als 'sailboat_model_v1.zip' gespeichert.")
        
    except KeyboardInterrupt:
        # Falls du das Training mit Strg+C abbrichst, speichert er trotzdem, was er gelernt hat!
        print("\n⚠️ Training abgebrochen. Speichere bisherigen Fortschritt...")
        model.save("sailboat_model_v1_interrupted")
        
    finally:
        # 6. Aufräumen
        rclpy.shutdown()

if __name__ == '__main__':
    main()