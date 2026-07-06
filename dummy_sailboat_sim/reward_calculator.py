from dummy_sailboat_sim.config import Config
import math
class RewardCalculator:
    def __init__(self):
        pass

    def calculate(self, state_dict: dict, action: list) -> tuple[float, bool]:
        """
        Berechnet die Belohnung (Reward) für den aktuellen Zustand.
        
        Args:
            state_dict (dict): Dictionary mit allen aktuellen Sensordaten.
            action (list): Die in diesem Schritt ausgeführte Aktion [delta_rudder, delta_sail].
            
        Returns:
            tuple[float, bool]: (reward, terminated)
        """
        current_dist = state_dict['current_dist']
        prev_dist = state_dict['prev_dist']
        
        # 1. Potential-Based Reward (Echte Annäherung anstelle von theoretischer VMG)
        # Wir messen die hart verdiente Meter-Ersparnis pro Zeitschritt und rechnen sie 
        # in eine effektive "Velocity Made Good" (m/s) um, damit die Gewichtung gleich bleibt.
        distance_reduction = prev_dist - current_dist
        effective_vmg = distance_reduction / Config.STEP_TIME_SEC
        
        # Belohnung primär über echte Annäherung
        reward = effective_vmg * Config.REWARD_VMG_MULTIPLIER

        # Action Jitter Penalty: Bestrafung für zu starkes Lenken / Segelziehen (Smoothness)
        reward += Config.PENALTY_ACTION_JITTER * (abs(float(action[0])) + abs(float(action[1])))
        
        # Time Penalty: Bestrafung für jeden vergangenen Zeitschritt (schneller ist besser)
        reward += Config.REWARD_TIME_PENALTY

        # Heel Penalty: Bestrafung für starke Krängung (Schräglage exponentiell)
        heel_angle = state_dict['heel_angle']
        reward += Config.PENALTY_HEEL * (heel_angle ** 2)

        terminated = False
        
        pos_x = state_dict['pos_x']
        pos_y = state_dict['pos_y']
        
        # Abbruchbedingungen und finale Rewards/Penalties
        if current_dist < Config.TARGET_REWARD_RADIUS: 
            reward += Config.REWARD_SUCCESS 
            terminated = True
        elif pos_x < Config.WORKSPACE_X_MIN or pos_x > Config.WORKSPACE_X_MAX or \
             pos_y < Config.WORKSPACE_Y_MIN or pos_y > Config.WORKSPACE_Y_MAX:
            reward += Config.REWARD_FAIL
            terminated = True
            
        return float(reward), terminated
