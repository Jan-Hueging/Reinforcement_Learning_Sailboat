import gymnasium as gym
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3
import math
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
        # [x_rel, y_rel, v_linear, v_angular, wind_speed, wind_angle_rel]
        self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)

        # 3. ROS2 Setup
        if not rclpy.ok():
            rclpy.init()
        self.node = Node('sailboat_gym_interface')

        self.pub_rudder = self.node.create_publisher(Float64, '/cmd_rudder', 10)
        self.pub_sail = self.node.create_publisher(Float64, '/cmd_sail', 10)

        self.node.create_subscription(Odometry, '/sensors/odom', self._odom_cb, 10)
        self.node.create_subscription(Vector3, '/sensors/apparent_wind', self._wind_cb, 10)

        self.current_odom = None
        self.current_wind = None

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

    def _odom_cb(self, msg):
        self.current_odom = msg

    def _wind_cb(self, msg):
        self.current_wind = msg

    def _get_obs(self):
        if self.current_odom is None or self.current_wind is None:
            return np.zeros(6, dtype=np.float32)

        pos = np.array([self.current_odom.pose.pose.position.x, self.current_odom.pose.pose.position.y])
        rel_pos = self.target_pos - pos
        
        obs_x = np.clip(rel_pos[0] / 100.0, -1.0, 1.0)
        obs_y = np.clip(rel_pos[1] / 100.0, -1.0, 1.0)
        obs_v_lin = np.clip(self.current_odom.twist.twist.linear.x / 5.0, 0.0, 1.0)
        obs_v_ang = np.clip(self.current_odom.twist.twist.angular.z / 1.0, -1.0, 1.0)
        obs_wind_s = np.clip(self.current_wind.x / 15.0, 0.0, 1.0)
        obs_wind_a = self.current_wind.y / math.pi

        return np.array([obs_x, obs_y, obs_v_lin, obs_v_ang, obs_wind_s, obs_wind_a], dtype=np.float32)

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
        
        pos = np.array([self.current_odom.pose.pose.position.x, self.current_odom.pose.pose.position.y])
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

        
        if self.current_odom is not None:
            pos = np.array([self.current_odom.pose.pose.position.x, self.current_odom.pose.pose.position.y])
            self.prev_dist = np.linalg.norm(self.target_pos - pos)
        else:
            self.prev_dist = np.linalg.norm(self.target_pos - np.array([Config.START_X, Config.START_Y]))

        return self._get_obs(), {}