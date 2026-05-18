import rclpy
from rclpy.node import Node
import cv2
import numpy as np
import math

from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3

class VisualizerNode(Node):
    def __init__(self):
        super().__init__('visualizer_node')

        self.window_name = "Sailboat Radar (God-Mode)"
        cv2.namedWindow(self.window_name)

        self.x, self.y, self.theta, self.speed = 0.0, 0.0, 0.0, 0.0
        self.wind_speed, self.wind_angle = 0.0, 0.0
        self.scale = 15.0
        self.current_rudder = 0.0
        self.current_sail = math.pi  # Standardwert: halb aufgefiert 
        self.debug_true_wind_speed = 5.0
        self.debug_true_wind_angle = math.pi

        # Publisher für die Steuerung
        self.pub_rudder = self.create_publisher(Float64, '/cmd_rudder', 10)
        self.pub_sail = self.create_publisher(Float64, '/cmd_sail', 10)
        self.pub_weather = self.create_publisher(Vector3, '/debug/true_wind', 10)

        # Subscriber für die Sensoren
        self.create_subscription(Odometry, '/sensors/odom', self.odom_cb, 10)
        self.create_subscription(Vector3, '/sensors/apparent_wind', self.wind_cb, 10)

        # Schieberegler für Boot-Steuerung
        cv2.createTrackbar('Ruder (-1 bis 1)', self.window_name, 100, 200, self.update_controls)
        cv2.createTrackbar('Segel (-1 bis 1)', self.window_name, 200, 200, self.update_controls)
        
        # Schieberegler für das Wetter
        cv2.createTrackbar('Wind Speed (m/s)', self.window_name, 5, 20, self.update_weather)
        cv2.createTrackbar('Wind Angle (Deg)', self.window_name, 180, 360, self.update_weather)

        self.create_timer(1.0 / 30.0, self.render_loop)
        self.get_logger().info('Radar hochgefahren! Fenster sollte offen sein.')

        # Speicher für das dynamische Ziel
        self.target_x = 0.0
        self.target_y = 0.0

        # Subscriber Ruder, Segel & Ziel
        self.create_subscription(Vector3, '/navigation/target', self.target_cb, 10)
        self.create_subscription(Float64, '/cmd_rudder', self.cmd_rudder_cb, 10)
        self.create_subscription(Float64, '/cmd_sail', self.cmd_sail_cb, 10)

    def odom_cb(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.speed = msg.twist.twist.linear.x
        z = msg.pose.pose.orientation.z
        w = msg.pose.pose.orientation.w
        self.theta = math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)

    def wind_cb(self, msg):
        self.wind_speed = msg.x
        self.wind_angle = msg.y 

    def update_controls(self, _):
        # Regler auslesen
        val_rudder = cv2.getTrackbarPos('Ruder (-1 bis 1)', self.window_name)
        val_sail = cv2.getTrackbarPos('Segel (-1 bis 1)', self.window_name)
        
        # Umrechnen und Senden (Ruder: -1 bis 1, Segel: 0 bis Pi)
        action_rudder = (val_rudder - 100.0) / 100.0 
        action_sail = (val_sail - 100.0) / 100.0 
        echtes_segel = ((action_sail + 1.0) / 2.0) * math.pi
        self.current_rudder = action_rudder * 0.785
        self.current_sail = echtes_segel
        
        self.pub_rudder.publish(Float64(data=action_rudder))
        self.pub_sail.publish(Float64(data=echtes_segel))

    def update_weather(self, _):
        # Wetter-Regler auslesen
        w_speed = float(cv2.getTrackbarPos('Wind Speed (m/s)', self.window_name))
        w_angle_deg = float(cv2.getTrackbarPos('Wind Angle (Deg)', self.window_name))
        
        # In Radiant umrechnen
        w_angle_rad = math.radians(w_angle_deg)
        
        # Lokal speichern für die Grafik
        self.debug_true_wind_speed = w_speed
        self.debug_true_wind_angle = w_angle_rad
        
        # An ROS2 senden
        self.pub_weather.publish(Vector3(x=w_speed, y=w_angle_rad, z=0.0))

    def render_loop(self):
        img = np.zeros((600, 600, 3), dtype=np.uint8)
        cx, cy = 300, 300 
        
        # Umrechnung Boot-Position
        px = int(cx + self.x * self.scale) % 600
        py = int(cy - self.y * self.scale) % 600

        # Dynamischer Zielpunkt
        t_px = int(cx + self.target_x * self.scale) % 600
        t_py = int(cy - self.target_y * self.scale) % 600
        
        # Ziel-Kreis und Text zeichnen
        cv2.circle(img, (t_px, t_py), 8, (0, 255, 255), -1) 
        cv2.putText(img, f"ZIEL ({self.target_x:.1f}, {self.target_y:.1f})", 
                    (t_px + 12, t_py - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Bootskörper zeichnen
        cv2.circle(img, (px, py), 10, (0, 255, 0), -1) 
        
        # Fahrtrichtung zeichnen
        nose_x = int(px + math.cos(self.theta) * 25)
        nose_y = int(py - math.sin(self.theta) * 25)
        cv2.line(img, (px, py), (nose_x, nose_y), (0, 255, 0), 2)
        
        # Wind-Pfeil zeichnen
        global_wind_angle = self.theta + self.wind_angle
        wind_x = int(px + math.cos(global_wind_angle) * (self.wind_speed * 5))
        wind_y = int(py - math.sin(global_wind_angle) * (self.wind_speed * 5))
        cv2.line(img, (px, py), (wind_x, wind_y), (255, 0, 0), 2)

        # Ruder zeichnen
        stern_x = int(px - math.cos(self.theta) * 10)
        stern_y = int(py + math.sin(self.theta) * 10)
        rudder_angle = self.theta + self.current_rudder
        rudder_end_x = int(stern_x - math.cos(rudder_angle) * 12)
        rudder_end_y = int(stern_y + math.sin(rudder_angle) * 12)
        cv2.line(img, (stern_x, stern_y), (rudder_end_x, rudder_end_y), (0, 0, 255), 3)

        # Segel zeichnen
        sail_angle = self.theta - self.current_sail
        sail_end_x = int(px - math.cos(sail_angle) * 10)
        sail_end_y = int(py + math.sin(sail_angle) * 10)
        cv2.line(img, (px, py), (sail_end_x, sail_end_y), (255, 255, 255), 2)

        # Texte für Telemetrie darstellen
        cv2.putText(img, f"Speed: {self.speed:.2f} m/s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Wind: {self.wind_speed:.1f} m/s", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
        cv2.putText(img, f"Ruder: {math.degrees(self.current_rudder):.0f} Deg", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Globalen Windindikator zeichnen
        compass_cx, compass_cy = 540, 60
        cv2.circle(img, (compass_cx, compass_cy), 30, (50, 50, 50), 1)
        tw_end_x = int(compass_cx - math.cos(self.debug_true_wind_angle) * 25)
        tw_end_y = int(compass_cy + math.sin(self.debug_true_wind_angle) * 25)
        cv2.arrowedLine(img, (compass_cx, compass_cy), (tw_end_x, tw_end_y), (255, 255, 0), 2, tipLength=0.3)
        cv2.putText(img, "TRUE WIND", (500, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        cv2.imshow(self.window_name, img)
        cv2.waitKey(1)

    def target_cb(self, msg):
        self.target_x = msg.x
        self.target_y = msg.y

    def cmd_rudder_cb(self, msg):
        # Aktualisiert Ruder-Anzeige im Radar
        self.current_rudder = msg.data

    def cmd_sail_cb(self, msg):
        # Aktualisiert Segel-Anzeige im Radar
        self.current_sail = msg.data
        
def main(args=None):
    rclpy.init(args=args)
    node = VisualizerNode()
    rclpy.spin(node)
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()