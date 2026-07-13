from dummy_sailboat_sim.config import Config
import math
class RewardCalculator:
    def __init__(self):
        self.latest_breakdown = {
            'VMG': 0.0, 'Jitter': 0.0, 'Time': 0.0, 'Heel': 0.0, 'Term': 0.0, 'Total': 0.0
        }

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
        
        # 1. Potential-Based Reward
        distance_reduction = prev_dist - current_dist
        effective_vmg = distance_reduction / Config.STEP_TIME_SEC
        r_vmg = effective_vmg * Config.REWARD_VMG_MULTIPLIER

        # Action Jitter Penalty (Zappeln)
        # Die Strafe wird nun auf die DIFFERENZ zur letzten Aktion berechnet, da die Aktion absolut ist.
        prev_action = state_dict.get('prev_action', action)
        action_delta_rudder = abs(float(action[0]) - float(prev_action[0]))
        action_delta_sail = abs(float(action[1]) - float(prev_action[1]))
        r_jitter = Config.PENALTY_ACTION_JITTER * (action_delta_rudder + action_delta_sail)
        
        # Time Penalty
        r_time = Config.REWARD_TIME_PENALTY

        # Heel Penalty
        heel_angle = state_dict['heel_angle']
        r_heel = Config.PENALTY_HEEL * (heel_angle ** 2)

        reward = r_vmg + r_jitter + r_time + r_heel
        r_term = 0.0

        terminated = False
        
        pos_x = state_dict['pos_x']
        pos_y = state_dict['pos_y']
        
        # Abbruchbedingungen und finale Rewards/Penalties
        if current_dist < Config.TARGET_REWARD_RADIUS: 
            r_term = Config.REWARD_SUCCESS 
            reward += r_term
            terminated = True
        elif current_dist > Config.MAX_DISTANCE_FROM_TARGET:
            r_term = Config.REWARD_FAIL
            reward += r_term
            terminated = True
            
        self.latest_breakdown = {
            'VMG': r_vmg,
            'Jitter': r_jitter,
            'Time': r_time,
            'Heel': r_heel,
            'Term': r_term,
            'Total': float(reward)
        }
            
        return float(reward), terminated
