#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_srvs.srv import Empty
from std_msgs.msg import Float64
from geometry_msgs.msg import Pose, Twist  # NEU: Nackte Pose und Twist importiert
import time

class BoatResetService(Node):
    def __init__(self):
        super().__init__('boat_reset_service')
        
        # --- SERVICE ---
        self.srv = self.create_service(Empty, 'reset_simulation', self.reset_callback)
        
        # --- PUBLISHER ---
        self.sail_pub = self.create_publisher(Float64, '/Segelstellung_Soll', 10)
        self.rudder_pub = self.create_publisher(Float64, '/Ruderstellung_Soll', 10)
        
        # KORREKTUR: Datentyp geändert auf geometry_msgs/msg/Pose (ohne Stamped/Header!)
        self.gz_pose_pub = self.create_publisher(Pose, '/model/opti_boot/set_pose', 10)
        
        # NEU: Publisher um die kinetische Energie (Geschwindigkeit) im Simulator zu nullen
        self.gz_twist_pub = self.create_publisher(Twist, '/model/opti_boot/cmd_vel', 10)
        
        self.get_logger().info('Reset-Service "/reset_simulation" ist aktiv und wartet auf Aufruf...')

    def reset_callback(self, request, response):
        self.get_logger().warn('Reset-Befehl empfangen! Teleportiere Boot und nulle Energie...')
        
        # 1. Schritt: Geschwindigkeit im Simulator schlagartig auf 0 setzen
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.linear.y = 0.0
        stop_msg.linear.z = 0.0
        stop_msg.angular.x = 0.0
        stop_msg.angular.y = 0.0
        stop_msg.angular.z = 0.0
        
        # 2. Schritt: Nackte Teleportations-Pose definieren
        teleport_msg = Pose()
        
        # KORREKTUR: .pose entfällt hier, da teleport_msg bereits vom Typ Pose ist!
        teleport_msg.position.x = 0.0
        teleport_msg.position.y = 0.0
        teleport_msg.position.z = 0.3  # Leicht erhöht für sauberen Wasser-Drop
        
        teleport_msg.orientation.x = 0.0
        teleport_msg.orientation.y = 0.0
        teleport_msg.orientation.z = 0.0
        teleport_msg.orientation.w = 1.0  # Blickrichtung Osten (Yaw = 0)
        
        # Befehle mehrfach feuern, um Netzwerk-Latenzen der Bridge abzufangen
        for _ in range(5):
            self.gz_twist_pub.publish(stop_msg)
            self.gz_pose_pub.publish(teleport_msg)
            time.sleep(0.02)

        # 3. Schritt: Aktuatoren in ROS zurücksetzen
        rudder_msg = Float64(data=0.0)
        self.rudder_pub.publish(rudder_msg)
        
        sail_msg = Float64(data=0.5)
        self.sail_pub.publish(sail_msg)
        
        self.get_logger().info('Boot erfolgreich im Ursprung fixiert. Segel auf 0.5 rad gefiert.')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = BoatResetService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
