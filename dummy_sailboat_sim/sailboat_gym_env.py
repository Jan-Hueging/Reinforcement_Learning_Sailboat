import gymnasium as gym
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3
import math
import time

class SailboatEnv(gym.Env):
    """
    Gymnasium Umgebung für ein Segelboot.
    Reward-Logik: Fortschritt zum Ziel (Differenz der Entfernung).
    """
    def __init__(self):
        super(SailboatEnv, self).__init__()

        # --- 1. ACTION SPACE ---
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)

        # --- 2. OBSERVATION SPACE ---
        # [x_rel, y_rel, v_linear, v_angular, wind_speed, wind_angle_rel]
        self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(6,), dtype=np.float32)

        # --- 3. ROS2 SETUP ---
        if not rclpy.ok():
            rclpy.init()
        self.node = Node('sailboat_gym_interface')

        self.pub_rudder = self.node.create_publisher(Float64, '/cmd_rudder', 10)
        self.pub_sail = self.node.create_publisher(Float64, '/cmd_sail', 10)

        self.node.create_subscription(Odometry, '/sensors/odom', self._odom_cb, 10)
        self.node.create_subscription(Vector3, '/sensors/apparent_wind', self._wind_cb, 10)

        self.current_odom = None
        self.current_wind = None

        # Publisher für das aktuelle Ziel (damit der Visualizer es zeichnen kann)
        self.pub_target = self.node.create_publisher(Vector3, '/navigation/target', 10)
        
        # Zielpunkt (50m in X-Richtung)
        self.target_pos = np.array([40.0, 30.0])
        
        # Speicher für die Entfernung im letzten Schritt
        self.prev_dist = 0.0
        self.current_step = 0 # NEU: Schrittzähler
        self.max_steps = 500  # NEU: Maximale Schritte pro Versuch

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
        # 1. Mapping
        rudder_val = float(action[0] * 0.785)
        sail_val = float(((action[1] + 1.0) / 2.0) * math.pi)

        # 2. Senden
        self.pub_rudder.publish(Float64(data=rudder_val))
        self.pub_sail.publish(Float64(data=sail_val))

        # 3. Warten auf Physik
        rclpy.spin_once(self.node, timeout_sec=0.05)
        
        # 4. Observation & Reward
        obs = self._get_obs()
        
        # Aktuelle Position und Distanz berechnen
        pos = np.array([self.current_odom.pose.pose.position.x, self.current_odom.pose.pose.position.y])
        current_dist = np.linalg.norm(self.target_pos - pos)
        
        # --- NEUE REWARD LOGIK ---
        # Belohnung = Verringerung der Distanz (Fortschritt)
        # Wenn current_dist < prev_dist, ist der Reward positiv.
        reward = self.prev_dist - current_dist
        
        # Aktuelle Distanz für den nächsten Schritt speichern
        self.prev_dist = current_dist

        # Das aktuelle Ziel veröffentlichen
        self.pub_target.publish(Vector3(x=float(self.target_pos[0]), y=float(self.target_pos[1]), z=0.0))
        
        # Abbruchbedingungen
        terminated = False
        if current_dist < 5.0: # Ziel erreicht
            reward += 20.0 # Bonus für Erfolg
            terminated = True
        elif current_dist > 150.0: # Zu weit weg/verlaufen
            reward -= 10.0
            terminated = True

        # --- ZEITLIMIT PRÜFEN ---
        self.current_step += 1
        truncated = False
        if self.current_step >= self.max_steps:
            truncated = True 
            
        # Wichtig: return-Zeile anpassen! (truncated statt False)
        return obs, float(reward), terminated, truncated, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0 # NEU: Zähler zurücksetzen
        
        # Boot anhalten (Dummy-Reset)
        self.pub_rudder.publish(Float64(data=0.0))
        self.pub_sail.publish(Float64(data=0.0))
        
        # Kurz warten, bis Daten fließen
        for _ in range(5):
            rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Initialdistanz für den ersten Schritt im neuen Lauf setzen
        if self.current_odom is not None:
            pos = np.array([self.current_odom.pose.pose.position.x, self.current_odom.pose.pose.position.y])
            self.prev_dist = np.linalg.norm(self.target_pos - pos)
        else:
            self.prev_dist = 50.0 # Standardwert

        return self._get_obs(), {}