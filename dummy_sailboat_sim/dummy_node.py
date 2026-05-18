import rclpy
from rclpy.node import Node
import math

# Nachrichten-Typen importieren
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3 
from dummy_sailboat_sim.config import Config
from std_srvs.srv import Empty

class DummySailboat(Node):
    def __init__(self):
        super().__init__('dummy_sailboat_node')
        
        # ==========================================
        # 1. INTERNE ZUSTÄNDE (Physik-Variablen)
        # ==========================================

        self.x = Config.START_X         # Startposition X
        self.y = Config.START_Y         # Startposition Y
        self.theta = Config.START_THETA # Ausrichtung des Bootes (0 = nach Osten)
        self.v = Config.START_V         # Vorwärtsgeschwindigkeit (m/s)
        self.heel_angle = 0.0           # Krängung
        
        # Start-Werte für den Wind (werden durch Subscriber überschrieben)
        self.true_wind_speed = Config.WIND_SPEED_DEFAULT     
        self.true_wind_dir = Config.WIND_ANGLE_DEFAULT    

        # Aktuelle Inputs
        self.cmd_rudder = 0.0 
        self.cmd_sail = 0.0   
        self.dt = Config.STEP_TIME_SEC

        self.srv_reset = self.create_service(Empty, '/reset_simulation', self.reset_callback)


        # ==========================================
        # 2. SCHNITTSTELLEN: INPUTS (Subscriber)
        # ==========================================

        self.sub_rudder = self.create_subscription(Float64, '/cmd_rudder', self.rudder_cb, 10)
        self.sub_sail = self.create_subscription(Float64, '/cmd_sail', self.sail_cb, 10)
        self.sub_true_wind = self.create_subscription(Vector3, '/debug/true_wind', self.true_wind_cb, 10)


        # ==========================================
        # 3. SCHNITTSTELLEN: OUTPUTS (Publisher)
        # ==========================================

        self.pub_odom = self.create_publisher(Odometry, '/sensors/odom', 10)
        self.pub_wind = self.create_publisher(Vector3, '/sensors/apparent_wind', 10)
        self.pub_heel = self.create_publisher(Float64, '/sensors/heel_angle', 10)
        self.timer = self.create_timer(self.dt, self.update_physics)

        self.get_logger().info('⚓ Dummy-Boot mit dynamischem Wind gestartet!')

    # --- Callbacks für Inputs ---
    def rudder_cb(self, msg):
        self.cmd_rudder = msg.data

    def sail_cb(self, msg):
        self.cmd_sail = msg.data

    def true_wind_cb(self, msg):
        """Winddaten vom Visualizer empfangen"""
        self.true_wind_speed = msg.x
        self.true_wind_dir = msg.y
        # self.get_logger().info(f'Wind geändert: {msg.x}m/s bei {math.degrees(msg.y):.1f}°')

    # --- Physik-Simulation  ---
    def update_physics(self):

        # 1. Kinematik
        # Drehung basierend auf Ruder und aktueller Fahrt
        turn_rate = -self.cmd_rudder * self.v * Config.DUMMY_RUDDER_EFFECT
        self.theta += turn_rate * self.dt
        
        # Position (Vektorzerlegung)
        self.x += self.v * math.cos(self.theta) * self.dt
        self.y += self.v * math.sin(self.theta) * self.dt

        # 2. Gefühlter Wind 
        tw_x = self.true_wind_speed * math.cos(self.true_wind_dir)
        tw_y = self.true_wind_speed * math.sin(self.true_wind_dir)
        bw_x = -self.v * math.cos(self.theta)
        bw_y = -self.v * math.sin(self.theta)
        
        # Beschleunigung und Geschwindigkeitsupdate
        aw_x, aw_y = tw_x + bw_x, tw_y + bw_y
        aw_speed = math.sqrt(aw_x**2 + aw_y**2)
        
        # Relativer Windwinkel zu Bootsnase
        aw_dir_global = math.atan2(aw_y, aw_x)
        aw_angle_relative = aw_dir_global - self.theta
        aw_angle_relative = (aw_angle_relative + math.pi) % (2 * math.pi) - math.pi

        # 3. Antrieb & Effizienz
        # Cosinus von 0 bedeutet 100% Effizienz
        efficiency = math.cos(self.cmd_sail - aw_angle_relative) 
        
        # Zielgeschwindigkeit (30% der Windgeschwindigkeit bei perfektem Segel)
        target_v = aw_speed * Config.DUMMY_SAIL_EFFICIENCY * max(0.0, efficiency) 

        
        # Trägheit
        self.v += (target_v - self.v) * Config.DUMMY_INERTIA
        
        # Krängung (Neigung zur Seite)
        self.heel_angle = aw_speed * math.sin(aw_angle_relative) * Config.DUMMY_HEEL_STIFFNESS


        # ==========================================
        # 4. DATEN SENDEN
        # ==========================================

        # Scheinbarer Wind
        self.pub_wind.publish(Vector3(x=float(aw_speed), y=float(aw_angle_relative), z=0.0))
        
        # Krängung
        self.pub_heel.publish(Float64(data=float(self.heel_angle)))

        # Odometrie
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom'
        odom.pose.pose.position.x, odom.pose.pose.position.y = self.x, self.y
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)
        odom.twist.twist.linear.x = float(self.v)
        odom.twist.twist.angular.z = float(turn_rate)
        self.pub_odom.publish(odom)

    def reset_callback(self, request, response):
        self.get_logger().info('🔄 Teleportiere Boot zurück zum Start...')
        self.x = Config.START_X
        self.y = Config.START_Y
        self.theta = Config.START_THETA
        self.v = Config.START_V
        self.heel_angle = 0.0
        self.cmd_rudder = 0.0
        self.cmd_sail = Config.INITIAL_SAIL_ANGLE
        return response

def main(args=None):
    rclpy.init(args=args)
    node = DummySailboat()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()