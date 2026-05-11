import rclpy
from rclpy.node import Node
import math

# Nachrichten-Typen importieren
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3 

class DummySailboat(Node):
    def __init__(self):
        super().__init__('dummy_sailboat_node')
        
        # ==========================================
        # 1. INTERNE ZUSTÄNDE (Physik-Variablen)
        # ==========================================
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0      # Ausrichtung des Bootes (0 = nach Osten)
        self.v = 0.0          # Vorwärtsgeschwindigkeit (m/s)
        self.heel_angle = 0.0 # Krängung
        
        # Start-Werte für den Wind (werden durch Subscriber überschrieben)
        self.true_wind_speed = 5.0      
        self.true_wind_dir = math.pi    

        # Aktuelle Inputs
        self.cmd_rudder = 0.0 
        self.cmd_sail = 0.0   
        self.dt = 0.1 # 10 Hz

        # ==========================================
        # 2. SCHNITTSTELLEN: INPUTS (Subscriber)
        # ==========================================
        self.sub_rudder = self.create_subscription(Float64, '/cmd_rudder', self.rudder_cb, 10)
        self.sub_sail = self.create_subscription(Float64, '/cmd_sail', self.sail_cb, 10)
        
        # DAS NEUE WETTER-OHR:
        self.sub_true_wind = self.create_subscription(Vector3, '/debug/true_wind', self.true_wind_cb, 10)

        # ==========================================
        # 3. SCHNITTSTELLEN: OUTPUTS (Publisher)
        # ==========================================
        self.pub_odom = self.create_publisher(Odometry, '/sensors/odom', 10)
        self.pub_wind = self.create_publisher(Vector3, '/sensors/apparent_wind', 10)
        self.pub_heel = self.create_publisher(Float64, '/sensors/heel_angle', 10)
        
        self.timer = self.create_timer(self.dt, self.update_physics)
        self.get_logger().info('⚓ Dummy-Boot mit dynamischem Wind gestartet!')

    # --- Callbacks für die Inputs ---
    def rudder_cb(self, msg):
        self.cmd_rudder = msg.data

    def sail_cb(self, msg):
        self.cmd_sail = msg.data

    def true_wind_cb(self, msg):
        """ Empfängt Winddaten vom God-Mode Visualizer """
        self.true_wind_speed = msg.x
        self.true_wind_dir = msg.y
        # Kleines Feedback im Terminal
        # self.get_logger().info(f'Wind geändert: {msg.x}m/s bei {math.degrees(msg.y):.1f}°')

    # --- Das Herzstück: Die Physik-Simulation  ---
    def update_physics(self):
        # 1. KINEMATIK
        # Drehung basierend auf Ruder und aktueller Fahrt
        turn_rate = -self.cmd_rudder * self.v * 0.5 
        self.theta += turn_rate * self.dt
        
        # Position (Vektorzerlegung)
        self.x += self.v * math.cos(self.theta) * self.dt
        self.y += self.v * math.sin(self.theta) * self.dt

        # 2. GEFÜHLTER WIND (Apparent Wind) 
        # Berechnet aus Wahrem Wind (True Wind) minus Eigenbewegung (Fahrtwind)
        tw_x = self.true_wind_speed * math.cos(self.true_wind_dir)
        tw_y = self.true_wind_speed * math.sin(self.true_wind_dir)
        
        bw_x = -self.v * math.cos(self.theta)
        bw_y = -self.v * math.sin(self.theta)
        
        aw_x, aw_y = tw_x + bw_x, tw_y + bw_y
        aw_speed = math.sqrt(aw_x**2 + aw_y**2)
        
        # Relativer Windwinkel zur Bootsnase
        aw_dir_global = math.atan2(aw_y, aw_x)
        aw_angle_relative = aw_dir_global - self.theta
        aw_angle_relative = (aw_angle_relative + math.pi) % (2 * math.pi) - math.pi

        # 3. ANTRIEB & EFFIZIENZ
        # Hier wird die Segelstellung (cmd_sail) mit dem Windwinkel (aw_angle_relative) verglichen.
        # Ein Cosinus von 0 (Winkeldifferenz = 0) bedeutet 100% Effizienz.
        efficiency = math.cos(self.cmd_sail - aw_angle_relative) 
        
        # Zielgeschwindigkeit (vereinfacht: 30% der Windgeschwindigkeit bei perfektem Segel)
        target_v = aw_speed * 0.3 * max(0.0, efficiency) 

        
        # Trägheit (Dämpfung der Beschleunigung)
        self.v += (target_v - self.v) * 0.1
        
        # Krängung (Neigung zur Seite)
        self.heel_angle = aw_speed * math.sin(aw_angle_relative) * 0.1

        # ==========================================
        # 4. DATEN SENDEN
        # ==========================================
        # Scheinbarer Wind (Wichtig für die KI!)
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

def main(args=None):
    rclpy.init(args=args)
    node = DummySailboat()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()