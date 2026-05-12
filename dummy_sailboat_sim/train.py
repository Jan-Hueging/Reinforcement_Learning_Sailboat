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
        # Wird bei jedem einzelnen Zeitschritt aufgerufe
        return True

    def _on_rollout_end(self) -> None:
        # Wird exakt am Ende jeder Iteration (nach z.B. 2048 Schritten) aufgerufen
        self.iteration_count += 1
        total_steps = self.model.num_timesteps
        print(f"\n--- 🏁 ITERATION {self.iteration_count} BEENDET | GESAMT-SCHRITTE (KILOMETERSTAND): {total_steps} ---")

def main():
    print("🧠 Initialisiere KI-Training...")
    
    # 1. ROS2 im Hintergrund starten
    rclpy.init()
    
    # 2. Die Umgebung (Mapping) erschaffen
    env = SailboatEnv()
    
    # 3. Das Gehirn (PPO Algorithmus) erschaffen
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=Config.LEARNING_RATE,
        n_steps=Config.N_STEPS
    )
    
    # NEU: 3. Den Spion aktivieren und als Variable speichern
    logger_callback = ProgressLoggerCallback()
    
    print(f"🚀 Training startet jetzt! Geplant: {Config.TOTAL_TIMESTEPS} Schritte.")
    
    try:
        # 4. Der eigentliche Trainings-Prozess
        model.learn(
            total_timesteps=Config.TOTAL_TIMESTEPS,
            callback=logger_callback,
            reset_num_timesteps=False
        )
        
        # 5. Gehirn speichern, wenn es fertig ist
        model.save(Config.MODEL_NAME)
        print(f"✅ Training beendet! Modell wurde als {Config.MODEL_NAME}.zip gespeichert.")
        
    except KeyboardInterrupt:
        # Falls das Training mit Strg+C abbricht, speichert er trotzdem
        print("\n⚠️ Training abgebrochen. Speichere bisherigen Fortschritt...")
        interrupted_name = f"{Config.MODEL_NAME}_interrupted"
        model.save(interrupted_name)
        print(f"💾 Gespeichert unter: {interrupted_name}.zip")
        
    finally:
        # 6. Aufräumen
        rclpy.shutdown()

if __name__ == '__main__':
    main()