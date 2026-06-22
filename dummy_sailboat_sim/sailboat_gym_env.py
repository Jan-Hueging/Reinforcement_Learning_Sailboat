import gymnasium as gym
import numpy as np
import rclpy
from rclpy.node import Node
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
        self.node = Node('sailboat_gym_interface')

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
        
        # Für Geschwindigkeitsberechnung aus GPS
        self.prev_gps = None
        self.prev_compass = 0.0
        self.prev_time = time.time()

        self.pub_target = self.node.create_publisher(Vector3, '/navigation/target', 10)
        
        # Fester Zielpunkt
        self.target_pos = np.array([40.0, 30.0])
        
        self.prev_dist = 0.0
        self.current_step = 0

        self.reset_client = self.node.create_client(Empty, '/reset_simulation')
        
        self.max_steps = Config.MAX_EPISODE_STEPS 

        # Gedächtnis für Delta-Steuerung
        self.current_rudder = Config.INITIAL_RUDDER_ANGLE
        self.current_sail = Config.INITIAL_SAIL_ANGLE
        
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
        current_time = time.time()
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

        self.prev_gps = Point(x=self.current_gps.x, y=self.current_gps.y, z=0.0)
        self.prev_compass = self.current_compass
        self.prev_time = current_time

        # 3. Observation Array normalisieren (-1 bis 1)
        obs_dist = np.clip(dist_to_target / 100.0, 0.0, 1.0) # 0 bis 1
        obs_angle = rel_angle_to_target / math.pi            # -1 bis 1
        obs_heel = np.clip(self.current_heel / (math.pi/4), -1.0, 1.0)
        obs_rudder = np.clip(self.current_rudder_ist / Config.MAX_RUDDER_ANGLE, -1.0, 1.0)
        obs_sail = np.clip(self.current_sail_ist / Config.MAX_SAIL_ANGLE, 0.0, 1.0) # 0 bis 1
        obs_wind_s = np.clip(self.current_wind_speed / 15.0, 0.0, 1.0)
        obs_wind_a = self.current_wind_dir / math.pi
        obs_v_lin = np.clip(v_linear / 5.0, 0.0, 1.0)
        obs_v_ang = np.clip(v_angular / 1.0, -1.0, 1.0)

        return np.array([obs_dist, obs_angle, obs_heel, obs_rudder, obs_sail, obs_wind_s, obs_wind_a, obs_v_lin, obs_v_ang], dtype=np.float32)

    def step(self, action):

        # action[0 & 1] sind die gewünschten Änderungen (-1 bis 1)
        rudder_delta = action[0] * Config.MAX_RUDDER_DELTA
        sail_delta = action[1] * Config.MAX_SAIL_DELTA

        # Delta auf IST addieren
        self.current_rudder += rudder_delta
        self.current_sail += sail_delta

        # Segel & Ruder begrenzen
        self.current_rudder = np.clip(self.current_rudder, -Config.MAX_RUDDER_ANGLE, Config.MAX_RUDDER_ANGLE)
        self.current_sail = np.clip(self.current_sail, 0.0, Config.MAX_SAIL_ANGLE)

        # Senden (neuen) Werte
        self.pub_rudder.publish(Float64(data=float(self.current_rudder)))
        self.pub_sail.publish(Float64(data=float(self.current_sail)))

        # Warten auf Physik
        rclpy.spin_once(self.node, timeout_sec=Config.STEP_TIME_SEC)
        
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
        reward, terminated = self.reward_calculator.calculate(current_dist, self.prev_dist, action)
        self.prev_dist = current_dist

        self.pub_target.publish(Vector3(x=float(self.target_pos[0]), y=float(self.target_pos[1]), z=0.0))


        self.current_step += 1
        truncated = False

        if self.current_step >= self.max_steps:
            truncated = True 
            
        return obs, float(reward), terminated, truncated, {}

    def reset(self, seed=None, options=None):

        while not self.reset_client.wait_for_service(timeout_sec=1.0):
            self.node.get_logger().info('Warte auf Reset-Service...')
    
        # Boot zurücksetzen
        self.reset_client.call_async(Empty.Request())

        super().reset(seed=seed)
        self.current_step = 0 
        
        self.current_rudder = Config.INITIAL_RUDDER_ANGLE
        self.current_sail = Config.INITIAL_SAIL_ANGLE
        
        self.pub_rudder.publish(Float64(data=float(self.current_rudder)))
        self.pub_sail.publish(Float64(data=float(self.current_sail)))
        
        for _ in range(5):
            rclpy.spin_once(self.node, timeout_sec=0.1)

        rand_x = np.random.uniform(Config.TARGET_SPAWN_X[0], Config.TARGET_SPAWN_X[1])
        rand_y = np.random.uniform(Config.TARGET_SPAWN_Y[0], Config.TARGET_SPAWN_Y[1])
        self.target_pos = np.array([rand_x, rand_y])
        
        # Visualizer mitteilen, wo neues Ziel ist
        self.pub_target.publish(Vector3(x=float(self.target_pos[0]), y=float(self.target_pos[1]), z=0.0))

        if self.current_gps is not None:
            pos = np.array([self.current_gps.x, self.current_gps.y])
            self.prev_dist = np.linalg.norm(self.target_pos - pos)
        else:
            self.prev_dist = np.linalg.norm(self.target_pos - np.array([Config.START_X, Config.START_Y]))

        return self._get_obs(), {}