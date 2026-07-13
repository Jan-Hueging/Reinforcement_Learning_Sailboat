import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
import math

# Nachrichten-Typen importieren
from std_msgs.msg import Float64
from geometry_msgs.msg import Point, Vector3 
from dummy_sailboat_sim.config import Config
from std_srvs.srv import Empty

class DummySailboat(Node):
    def __init__(self):
        super().__init__('dummy_sailboat_node', parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        
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

        self.sub_rudder = self.create_subscription(Float64, Config.TOPIC_RUDDER_SOLL, self.rudder_cb, 10)
        self.sub_sail = self.create_subscription(Float64, Config.TOPIC_SAIL_SOLL, self.sail_cb, 10)
        
        # Wind kommt weiterhin vom Debug-Visualizer
        self.sub_true_wind = self.create_subscription(Vector3, '/debug/true_wind', self.true_wind_cb, 10)

        # ==========================================
        # 3. SCHNITTSTELLEN: OUTPUTS (Publisher)
        # ==========================================

        self.pub_gps = self.create_publisher(Point, Config.TOPIC_GPS, 10)
        self.pub_compass = self.create_publisher(Float64, Config.TOPIC_COMPASS, 10)
        self.pub_heel = self.create_publisher(Float64, Config.TOPIC_HEEL, 10)
        self.pub_rudder_ist = self.create_publisher(Float64, Config.TOPIC_RUDDER_IST, 10)
        self.pub_sail_ist = self.create_publisher(Float64, Config.TOPIC_SAIL_IST, 10)
        self.pub_wind_speed = self.create_publisher(Float64, Config.TOPIC_WIND_SPEED, 10)
        self.pub_wind_dir = self.create_publisher(Float64, Config.TOPIC_WIND_DIR, 10)
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
        # Drehung basierend auf Ruder (jetzt in rad) und aktueller Fahrt
        norm_rudder = self.cmd_rudder / Config.MAX_RUDDER_ANGLE_RAD
        turn_rate = -norm_rudder * self.v * Config.DUMMY_RUDDER_EFFECT
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
        # Die empfangene cmd_sail ist die Schotlänge (in Radiant).
        # Der echte Baumwinkel schwingt je nach Wind auf die Leeseite.
        # aw_angle_relative ist die Richtung, in die der Wind weht.
        # Das Segel wird in genau diese Richtung gedrückt.
        sheet_rad = self.cmd_sail
        actual_sail_rad = math.copysign(sheet_rad, aw_angle_relative)
        
        # Cosinus von 0 bedeutet 100% Effizienz
        efficiency = math.cos(actual_sail_rad - aw_angle_relative) 
        
        # Zielgeschwindigkeit (30% der Windgeschwindigkeit bei perfektem Segel)
        target_v = aw_speed * Config.DUMMY_SAIL_EFFICIENCY * max(0.0, efficiency) 

        
        # Trägheit
        self.v += (target_v - self.v) * Config.DUMMY_INERTIA
        
        # Krängung (Neigung zur Seite)
        self.heel_angle = aw_speed * math.sin(aw_angle_relative) * Config.DUMMY_HEEL_STIFFNESS


        # ==========================================
        # 4. DATEN SENDEN
        # ==========================================

        # GPS Position
        gps_msg = Point()
        gps_msg.x = float(self.x)
        gps_msg.y = float(self.y)
        gps_msg.z = 0.0
        self.pub_gps.publish(gps_msg)

        # Kompass (Ausrichtung)
        self.pub_compass.publish(Float64(data=float(self.theta)))

        # Neigung (Krängung)
        self.pub_heel.publish(Float64(data=float(self.heel_angle)))

        # Scheinbarer Wind (Gemessen)
        self.pub_wind_speed.publish(Float64(data=float(aw_speed)))
        self.pub_wind_dir.publish(Float64(data=float(aw_angle_relative)))

        # Aktuelle Stellung von Ruder und Segel
        self.pub_rudder_ist.publish(Float64(data=float(self.cmd_rudder)))
        self.pub_sail_ist.publish(Float64(data=float(self.cmd_sail)))

    def reset_callback(self, request, response):
        self.get_logger().info('🔄 Teleportiere Boot zurück zum Start...')
        self.x = Config.START_X
        self.y = Config.START_Y
        self.theta = Config.START_THETA
        self.v = Config.START_V
        self.heel_angle = 0.0
        self.cmd_rudder = 0.0
        self.cmd_sail = Config.INITIAL_SAIL_ANGLE_RAD
        return response

def main(args=None):
    rclpy.init(args=args)
    node = DummySailboat()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()