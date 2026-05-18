import rclpy
from stable_baselines3 import PPO
from sailboat_gym_env import SailboatEnv # Importiert deine Umgebung
from stable_baselines3.common.callbacks import BaseCallback
from dummy_sailboat_sim.config import Config

class ProgressLoggerCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(ProgressLoggerCallback, self).__init__(verbose)
        self.iteration_count = 0

    def _on_step(self) -> bool:
        # Wird bei jedem einzelnen Zeitschritt aufgerufen
        return True

    def _on_rollout_end(self) -> None:
        # Wird am Ende jeder Iteration aufgerufen
        self.iteration_count += 1
        total_steps = self.model.num_timesteps
        print(f"\n--- 🏁 ITERATION {self.iteration_count} BEENDET | GESAMT-SCHRITTE (KILOMETERSTAND): {total_steps} ---")

def main():
    print("🧠 Initialisiere KI-Training...")
    
    # 1. ROS2 im Hintergrund starten
    rclpy.init()
    
    # 2. Umgebung (Mapping) erstellen
    env = SailboatEnv()
    
    # 3. Gehirn (PPO Algorithmus) erstellen
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=Config.LEARNING_RATE,
        n_steps=Config.N_STEPS
    )
    
    # 3. "Spion" aktivieren & als Variable speichern
    logger_callback = ProgressLoggerCallback()
    
    print(f"🚀 Training startet jetzt! Geplant: {Config.TOTAL_TIMESTEPS} Schritte.")
    
    try:
        # 4. Eigentlicher Trainings-Prozess
        model.learn(
            total_timesteps=Config.TOTAL_TIMESTEPS,
            callback=logger_callback,
            reset_num_timesteps=False
        )
        
        # 5. Speichern, wenn fertig
        model.save(Config.MODEL_NAME)
        print(f"✅ Training beendet! Modell wurde als {Config.MODEL_NAME}.zip gespeichert.")
        
    except KeyboardInterrupt:
        # Falls das Training mit Strg+C abbricht trotzdem speichern
        print("\n⚠️ Training abgebrochen. Speichere bisherigen Fortschritt...")
        interrupted_name = f"{Config.MODEL_NAME}_interrupted"
        model.save(interrupted_name)
        print(f"💾 Gespeichert unter: {interrupted_name}.zip")
        
    finally:
        # 6. Aufräumen
        rclpy.shutdown()

if __name__ == '__main__':
    main()