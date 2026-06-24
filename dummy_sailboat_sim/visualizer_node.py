import rclpy
from rclpy.node import Node
import cv2
import numpy as np
import math

from std_msgs.msg import Float64
from geometry_msgs.msg import Point, Vector3
from dummy_sailboat_sim.config import Config

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
        self.pub_rudder = self.create_publisher(Float64, Config.TOPIC_RUDDER_SOLL, 10)
        self.pub_sail = self.create_publisher(Float64, Config.TOPIC_SAIL_SOLL, 10)
        self.pub_weather = self.create_publisher(Vector3, '/debug/true_wind', 10)

        # Subscriber für die Sensoren
        self.create_subscription(Point, Config.TOPIC_GPS, self.gps_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_COMPASS, self.compass_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_WIND_SPEED, self.wind_speed_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_WIND_DIR, self.wind_dir_cb, 10)

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
        self.create_subscription(Float64, Config.TOPIC_RUDDER_IST, self.cmd_rudder_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_SAIL_IST, self.cmd_sail_cb, 10)

    def gps_cb(self, msg):
        self.x = msg.x
        self.y = msg.y

    def compass_cb(self, msg):
        self.theta = msg.data

    def wind_speed_cb(self, msg):
        self.wind_speed = msg.data

    def wind_dir_cb(self, msg):
        self.wind_angle = msg.data

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
        WIDTH, HEIGHT = 1000, 1000
        # Wasser-Hintergrund (Tiefblau)
        img = np.full((HEIGHT, WIDTH, 3), (60, 30, 10), dtype=np.uint8)
        cx, cy = int(WIDTH * 0.15), HEIGHT // 2
        
        # Gitternetz (Ozean-Grid)
        for i in range(0, WIDTH, 50):
            cv2.line(img, (i, 0), (i, HEIGHT), (80, 45, 20), 1)
            cv2.line(img, (0, i), (WIDTH, i), (80, 45, 20), 1)
        
        # Umrechnung Boot-Position
        self.scale = 20.0
        px = int(cx + self.x * self.scale) % WIDTH
        py = int(cy - self.y * self.scale) % HEIGHT

        # Dynamischer Zielpunkt
        t_px = int(cx + self.target_x * self.scale) % WIDTH
        t_py = int(cy - self.target_y * self.scale) % HEIGHT
        
        # Ziel-Marker (Bojen-Look)
        cv2.circle(img, (t_px, t_py), 12, (0, 165, 255), -1) # Orange
        cv2.circle(img, (t_px, t_py), 16, (0, 255, 255), 2)  # Gelber Ring
        cv2.putText(img, f"TARGET", (t_px - 25, t_py - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, f"({self.target_x:.1f}, {self.target_y:.1f})", (t_px - 35, t_py + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)

        # Boot Rumpf (Polygon)
        hull_length = 30
        hull_width = 12
        boat_pts = np.array([
            [px + math.cos(self.theta) * hull_length, py - math.sin(self.theta) * hull_length], # Nase
            [px + math.cos(self.theta - 2.5) * hull_width, py - math.sin(self.theta - 2.5) * hull_width], # Heck rechts
            [px - math.cos(self.theta) * (hull_length*0.2), py + math.sin(self.theta) * (hull_length*0.2)], # Heck mitte
            [px + math.cos(self.theta + 2.5) * hull_width, py - math.sin(self.theta + 2.5) * hull_width], # Heck links
        ], np.int32)
        cv2.fillConvexPoly(img, boat_pts, (200, 200, 200))
        cv2.polylines(img, [boat_pts], True, (255, 255, 255), 2)

        # Scheinbarer Wind-Pfeil (entfernt nach User-Wunsch)
        # (Wird nicht mehr gezeichnet, da er am Boot stört)

        # Ruder
        stern_x = int(px - math.cos(self.theta) * (hull_length*0.2))
        stern_y = int(py + math.sin(self.theta) * (hull_length*0.2))
        rudder_angle = self.theta + self.current_rudder
        rudder_end_x = int(stern_x - math.cos(rudder_angle) * 15)
        rudder_end_y = int(stern_y + math.sin(rudder_angle) * 15)
        cv2.line(img, (stern_x, stern_y), (rudder_end_x, rudder_end_y), (0, 0, 255), 3)

        # Segel (Weiß) - optisch um 90 Grad gedreht für intuitive Anzeige
        sail_angle = self.theta - self.current_sail + (math.pi / 2)
        sail_end_x = int(px - math.cos(sail_angle) * 25)
        sail_end_y = int(py + math.sin(sail_angle) * 25)
        cv2.line(img, (px, py), (sail_end_x, sail_end_y), (255, 255, 255), 4)

        # HUD / Telemetrie (halbtransparenter Hintergrund)
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (250, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        
        cv2.putText(img, "TELEMETRY", (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "-" * 30, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(img, f"Speed: {self.speed:.2f} m/s", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"A-Wind: {self.wind_speed:.1f} m/s", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"Rudder: {math.degrees(self.current_rudder):.0f} deg", (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 1, cv2.LINE_AA)

        # Globaler True Windindikator oben rechts
        compass_cx, compass_cy = WIDTH - 80, 80
        cv2.circle(img, (compass_cx, compass_cy), 40, (30, 30, 30), -1)
        cv2.circle(img, (compass_cx, compass_cy), 40, (100, 100, 100), 2)
        cv2.putText(img, "N", (compass_cx - 5, compass_cy - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
        
        tw_end_x = int(compass_cx - math.cos(self.debug_true_wind_angle) * 30)
        tw_end_y = int(compass_cy + math.sin(self.debug_true_wind_angle) * 30)
        cv2.arrowedLine(img, (compass_cx, compass_cy), (tw_end_x, tw_end_y), (255, 150, 0), 3, tipLength=0.3)
        cv2.putText(img, "T-WIND", (compass_cx - 25, compass_cy + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 150, 0), 1, cv2.LINE_AA)

        cv2.imshow(self.window_name, img)
        
        # Fenster schließen ermöglichen (ESC Taste beendet Node)
        key = cv2.waitKey(1)
        if key == 27:
            rclpy.shutdown()

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