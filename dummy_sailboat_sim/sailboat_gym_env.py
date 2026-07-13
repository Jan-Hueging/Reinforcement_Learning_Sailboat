import gymnasium as gym
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import Float64
from geometry_msgs.msg import Point, Vector3
import math
import time
from dummy_sailboat_sim.config import Config
from dummy_sailboat_sim.reward_calculator import RewardCalculator
from std_srvs.srv import Empty

class SailboatEnv(gym.Env):
    """ Gymnasium Umgebung fürs Segelboot """

    def __init__(self):
        super(SailboatEnv, self).__init__()

        # 1. Action Space
        # KI bekommt Änderungsraten (-1.0 bis 1.0)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)

        # 2. Observation Space
        # [Distanz_zum_Ziel, Winkel_zum_Ziel, Neigung, Ruder_Ist, Segel_Ist, Wind_Speed, Wind_Dir, v_linear, v_angular]
        self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(9,), dtype=np.float32)

        # 3. ROS2 Setup
        if not rclpy.ok():
            rclpy.init()
        self.node = Node('sailboat_gym_interface', parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, False)])

        self.pub_rudder = self.node.create_publisher(Float64, Config.TOPIC_RUDDER_SOLL, 10)
        self.pub_sail = self.node.create_publisher(Float64, Config.TOPIC_SAIL_SOLL, 10)

        # Subscriber für die aufgeteilten Topics
        self.node.create_subscription(Point, Config.TOPIC_GPS, self._gps_cb, 10)
        self.node.create_subscription(Float64, Config.TOPIC_COMPASS, self._compass_cb, 10)
        self.node.create_subscription(Float64, Config.TOPIC_HEEL, self._heel_cb, 10)
        self.node.create_subscription(Float64, Config.TOPIC_RUDDER_IST, self._rudder_ist_cb, 10)
        self.node.create_subscription(Float64, Config.TOPIC_SAIL_IST, self._sail_ist_cb, 10)
        self.node.create_subscription(Float64, Config.TOPIC_WIND_SPEED, self._wind_speed_cb, 10)
        self.node.create_subscription(Float64, Config.TOPIC_WIND_DIR, self._wind_dir_cb, 10)

        # Aktuelle Sensorwerte
        self.current_gps = None
        self.current_compass = 0.0
        self.current_heel = 0.0
        self.current_rudder_ist = 0.0
        self.current_sail_ist = 0.0
        self.current_wind_speed = 0.0
        self.current_wind_dir = 0.0
        self.current_v_linear = 0.0
        self.current_rel_angle = 0.0
        
        # Für Geschwindigkeitsberechnung aus GPS
        self.prev_gps = None
        self.prev_compass = 0.0
        self.prev_time = self.node.get_clock().now().nanoseconds / 1e9

        self.pub_target = self.node.create_publisher(Vector3, '/navigation/target', 10)
        
        # Generiere ein zufälliges Ziel (relativ zum Start)
        radius = float(np.random.uniform(Config.TARGET_SPAWN_RADIUS[0], Config.TARGET_SPAWN_RADIUS[1]))
        angle = float(np.random.uniform(-math.pi, math.pi))
        self.target_pos = np.array([radius * math.cos(angle), radius * math.sin(angle)])
        
        self.prev_dist = 0.0
        self.current_step = 0
        self.prev_action = np.array([0.0, 0.0])
        
        self.max_steps = Config.MAX_EPISODE_STEPS 

        # Gedächtnis für Delta-Steuerung (Normiert auf -1 bis 1)
        self.current_rudder_norm = 0.0
        self.current_sail_norm = 0.0
        
        self.reward_calculator = RewardCalculator()

    def _gps_cb(self, msg):
        self.current_gps = msg

    def _compass_cb(self, msg):
        self.current_compass = msg.data

    def _heel_cb(self, msg):
        self.current_heel = msg.data
        
    def _rudder_ist_cb(self, msg):
        self.current_rudder_ist = msg.data
        
    def _sail_ist_cb(self, msg):
        self.current_sail_ist = msg.data

    def _wind_speed_cb(self, msg):
        self.current_wind_speed = msg.data
        
    def _wind_dir_cb(self, msg):
        self.current_wind_dir = msg.data

    def _get_obs(self):
        if self.current_gps is None:
            return np.zeros(9, dtype=np.float32)

        # 1. Distanz und Winkel zum Ziel berechnen
        pos = np.array([self.current_gps.x, self.current_gps.y])
        rel_pos = self.target_pos - pos
        dist_to_target = np.linalg.norm(rel_pos)
        angle_to_target = math.atan2(rel_pos[1], rel_pos[0])
        rel_angle_to_target = angle_to_target - self.current_compass
        rel_angle_to_target = (rel_angle_to_target + math.pi) % (2 * math.pi) - math.pi

        # 2. Geschwindigkeit aus GPS/Kompass-Historie berechnen
        current_time = self.node.get_clock().now().nanoseconds / 1e9
        dt = current_time - self.prev_time
        v_linear = 0.0
        v_angular = 0.0
        
        if self.prev_gps is not None and dt > 0.001:
            dx = self.current_gps.x - self.prev_gps.x
            dy = self.current_gps.y - self.prev_gps.y
            dist_moved = math.sqrt(dx**2 + dy**2)
            v_linear = dist_moved / dt
            
            d_theta = self.current_compass - self.prev_compass
            d_theta = (d_theta + math.pi) % (2 * math.pi) - math.pi
            v_angular = d_theta / dt

        self.current_v_linear = v_linear
        self.current_rel_angle = rel_angle_to_target

        self.prev_gps = Point(x=self.current_gps.x, y=self.current_gps.y, z=0.0)
        self.prev_compass = self.current_compass
        self.prev_time = current_time

        # 3. Observation Array normalisieren (-1 bis 1)
        obs_dist = np.clip(dist_to_target / 100.0, 0.0, 1.0) # 0 bis 1
        obs_angle = rel_angle_to_target / math.pi            # -1 bis 1
        obs_heel = np.clip(self.current_heel / (math.pi/4), -1.0, 1.0)
        # Ist-Werte auf -1 bis 1 normieren
        obs_rudder = np.clip(self.current_rudder_ist / Config.MAX_RUDDER_ANGLE_RAD, -1.0, 1.0)
        obs_sail = np.clip((self.current_sail_ist / (Config.MAX_SAIL_ANGLE_RAD / 2.0)) - 1.0, -1.0, 1.0)
        obs_wind_s = np.clip(self.current_wind_speed / 15.0, 0.0, 1.0)
        obs_wind_a = self.current_wind_dir / math.pi
        obs_v_lin = np.clip(v_linear / 5.0, 0.0, 1.0)
        obs_v_ang = np.clip(v_angular / 1.0, -1.0, 1.0)

        return np.array([obs_dist, obs_angle, obs_heel, obs_rudder, obs_sail, obs_wind_s, obs_wind_a, obs_v_lin, obs_v_ang], dtype=np.float32)

    def step(self, action):

        # action[0 & 1] sind nun ABSOLUTE SOLL-WERTE (-1 bis 1)
        self.current_rudder_norm = float(np.clip(action[0], -1.0, 1.0))
        self.current_sail_norm = float(np.clip(action[1], -1.0, 1.0))

        # Umrechnen in Radiant für die Topics
        pub_rudder_rad = float(self.current_rudder_norm * Config.MAX_RUDDER_ANGLE_RAD)
        
        # Segel von [-1, 1] auf [MIN_SAIL_ANGLE, MAX_SAIL_ANGLE] interpolieren
        sail_range = Config.MAX_SAIL_ANGLE_RAD - Config.MIN_SAIL_ANGLE_RAD
        pub_sail_rad = float(Config.MIN_SAIL_ANGLE_RAD + ((self.current_sail_norm + 1.0) / 2.0) * sail_range)

        # Senden (neuen) Werte
        self.pub_rudder.publish(Float64(data=pub_rudder_rad))
        self.pub_sail.publish(Float64(data=pub_sail_rad))

        # Warten, bis die Simulation (Gazebo) wirklich die Zeit STEP_TIME_SEC simuliert hat.
        # Da wir use_sim_time=False nutzen, ist dies die echte Zeit.
        start_time = self.node.get_clock().now()
        import rclpy.duration
        target_time = start_time + rclpy.duration.Duration(seconds=Config.STEP_TIME_SEC)
        
        while rclpy.ok():
            current_time = self.node.get_clock().now()
            if current_time >= target_time:
                break
            rclpy.spin_once(self.node, timeout_sec=0.01)
        
        # Observation & Reward
        obs = self._get_obs()
        
        if self.current_gps is not None:
            pos = np.array([self.current_gps.x, self.current_gps.y])
        else:
            pos = np.array([Config.START_X, Config.START_Y])
            
        current_dist = np.linalg.norm(self.target_pos - pos)
        
        # ==========================================
        # REWARD-BERECHNUNG (ausgelagert)
        # ==========================================
        state_dict = {
            'pos_x': pos[0],
            'pos_y': pos[1],
            'current_dist': current_dist,
            'prev_dist': self.prev_dist,
            'v_linear': self.current_v_linear,
            'angle_to_target': self.current_rel_angle,
            'heel_angle': self.current_heel,
            'prev_action': self.prev_action
        }
        reward, terminated = self.reward_calculator.calculate(state_dict, action)
        self.prev_dist = current_dist
        self.prev_action = np.copy(action)

        self.pub_target.publish(Vector3(x=float(self.target_pos[0]), y=float(self.target_pos[1]), z=0.0))


        self.current_step += 1
        truncated = False

        if self.current_step >= self.max_steps:
            truncated = True 
            
        return obs, float(reward), terminated, truncated, {}

    def reset(self, seed=None, options=None):

        # 1. Bestimme die aktuelle Position des Bootes
        if self.current_gps is not None:
            boat_x = self.current_gps.x
            boat_y = self.current_gps.y
        else:
            boat_x = 0.0
            boat_y = 0.0

        # 2. Generiere ein neues zufälliges Ziel RELATIV zur aktuellen Bootsposition (360 Grad im Umkreis)
        radius = float(np.random.uniform(Config.TARGET_SPAWN_RADIUS[0], Config.TARGET_SPAWN_RADIUS[1]))
        angle = float(np.random.uniform(-math.pi, math.pi))
        self.target_pos = np.array([boat_x + radius * math.cos(angle), boat_y + radius * math.sin(angle)])
        
        # Teile dem Visualizer schon jetzt das Ziel mit
        self.pub_target.publish(Vector3(x=float(self.target_pos[0]), y=float(self.target_pos[1]), z=0.0))
        rclpy.spin_once(self.node, timeout_sec=0.1)
    
        # (Es gibt KEINEN Aufruf von /reset_simulation mehr! Boot segelt einfach weiter)

        super().reset(seed=seed)
        self.current_step = 0 
        self.prev_time = self.node.get_clock().now().nanoseconds / 1e9
        
        self.current_rudder_norm = 0.0
        self.current_sail_norm = 0.0
        self.prev_action = np.array([0.0, 0.0])
        
        pub_rudder_rad = float(self.current_rudder_norm * Config.MAX_RUDDER_ANGLE_RAD)
        sail_range = Config.MAX_SAIL_ANGLE_RAD - Config.MIN_SAIL_ANGLE_RAD
        pub_sail_rad = float(Config.MIN_SAIL_ANGLE_RAD + ((self.current_sail_norm + 1.0) / 2.0) * sail_range)
        
        self.pub_rudder.publish(Float64(data=pub_rudder_rad))
        self.pub_sail.publish(Float64(data=pub_sail_rad))
        
        # Kurz warten, damit die Simulation die Nachrichten verarbeitet
        start_time = self.node.get_clock().now()
        target_time = start_time + rclpy.duration.Duration(seconds=0.5)
        while rclpy.ok():
            if self.node.get_clock().now() >= target_time:
                break
            rclpy.spin_once(self.node, timeout_sec=0.01)

        self.pub_target.publish(Vector3(x=float(self.target_pos[0]), y=float(self.target_pos[1]), z=0.0))

        if self.current_gps is not None:
            pos = np.array([self.current_gps.x, self.current_gps.y])
            self.prev_dist = np.linalg.norm(self.target_pos - pos)
        else:
            self.prev_dist = np.linalg.norm(self.target_pos - np.array([Config.START_X, Config.START_Y]))

        return self._get_obs(), {}