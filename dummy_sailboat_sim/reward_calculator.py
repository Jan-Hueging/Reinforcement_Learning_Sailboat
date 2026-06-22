from dummy_sailboat_sim.config import Config

class RewardCalculator:
    def __init__(self):
        pass

    def calculate(self, current_dist: float, prev_dist: float, action: list) -> tuple[float, bool]:
        """
        Berechnet die Belohnung (Reward) für den aktuellen Zustand.
        
        Args:
            current_dist (float): Aktuelle Distanz zum Ziel.
            prev_dist (float): Vorherige Distanz zum Ziel.
            action (list): Die in diesem Schritt ausgeführte Aktion [delta_rudder, delta_sail].
            
        Returns:
            tuple[float, bool]: (reward, terminated)
        """
        # Distanz-Reward: Belohnung dafür, dass wir dem Ziel näher gekommen sind
        reward = prev_dist - current_dist

        # Action Jitter Penalty: Bestrafung für zu starkes Lenken / Segelziehen (Smoothness)
        reward += Config.PENALTY_ACTION_JITTER * (abs(float(action[0])) + abs(float(action[1])))
        
        # Time Penalty: Bestrafung für jeden vergangenen Zeitschritt (schneller ist besser)
        reward += Config.REWARD_TIME_PENALTY

        terminated = False
        
        # Abbruchbedingungen und finale Rewards/Penalties
        if current_dist < Config.TARGET_REWARD_RADIUS: 
            reward += Config.REWARD_SUCCESS 
            terminated = True
        elif current_dist > Config.OUT_OF_BOUNDS_RADIUS: 
            reward += Config.REWARD_FAIL
            terminated = True
            
        return float(reward), terminated
