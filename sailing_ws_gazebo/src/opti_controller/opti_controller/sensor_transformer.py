import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState, NavSatFix
from geometry_msgs.msg import Vector3, Point  # NEU: Point importiert
from std_msgs.msg import Float64
import math

class SensorTransformer(Node):
    def __init__(self):
        super().__init__('sensor_transformer')
        
        # --- SUBSCRIBER ---
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.joint_sub = self.create_subscription(JointState, '/world/sydney_regatta/model/opti_boot/joint_state', self.joint_callback, 10)
        self.wind_sub = self.create_subscription(Vector3, '/wind', self.wind_callback, 10)
        self.gps_sub = self.create_subscription(NavSatFix, '/gps/data', self.gps_callback, 10)
            
        # --- PUBLISHER ---
        self.kraengung_pub = self.create_publisher(Float64, '/Neigung', 10)
        self.kompass_pub = self.create_publisher(Float64, '/Kompass', 10)
        self.ruder_aktuell_pub = self.create_publisher(Float64, '/Ruderstellung_Ist', 10)
        self.segel_aktuell_pub = self.create_publisher(Float64, '/Segelstellung_Ist', 10)
        self.wind_speed_pub = self.create_publisher(Float64, '/Windgeschwindigkeit', 10)
        self.wind_dir_pub = self.create_publisher(Float64, '/Windrichtung', 10)
        
        # KORREKTUR: Publisher stellt nun geometry_msgs/msg/Point bereit
        self.position_pub = self.create_publisher(Point, '/Position', 10)
        
        self.get_logger().info('Erweiterter Sensor-Transformer mit Wind- und GPS-Punktkonvertierung gestartet...')

    def imu_callback(self, msg):
        x, y, z, w = msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w
        roll_rad = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        yaw_rad = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        
        self.kraengung_pub.publish(Float64(data=roll_rad))
        self.kompass_pub.publish(Float64(data=yaw_rad))

    def joint_callback(self, msg):
        for i, name in enumerate(msg.name):
            if name == 'rudder_joint':
                self.ruder_aktuell_pub.publish(Float64(data=msg.position[i]))
            elif name == 'sail_joint':
                self.segel_aktuell_pub.publish(Float64(data=msg.position[i]))

    def wind_callback(self, msg):
        wind_speed = math.sqrt(msg.x**2 + msg.y**2)
        
        # Koordinatentransformation: Nullpunkt-Shift auf Osten (-y)
        wind_direction_rad = math.atan2(msg.y, msg.x)
        
        if wind_direction_rad > math.pi:
            wind_direction_rad -= 2.0 * math.pi
        elif wind_direction_rad < -math.pi:
            wind_direction_rad += 2.0 * math.pi
        
        self.wind_speed_pub.publish(Float64(data=wind_speed))
        self.wind_dir_pub.publish(Float64(data=wind_direction_rad))

    def gps_callback(self, msg):
        # KORREKTUR: Nutzt jetzt den Point-Datentyp
        pos_msg = Point()
        pos_msg.x = msg.longitude  # Longitude auf x-Achse
        pos_msg.y = msg.latitude   # Latitude auf y-Achse
        pos_msg.z = 0.0            # Konstante z-Höhe auf 0 gesetzt
        
        self.position_pub.publish(pos_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SensorTransformer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
