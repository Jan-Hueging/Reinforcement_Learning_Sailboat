#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Vector3

class StaticWindPublisher(Node):
    def __init__(self):
        super().__init__('static_wind_publisher')
        
        # Publisher auf dem gebrückten Wind-Topic
        self.wind_pub = self.create_publisher(Vector3, '/wind', 10)
        
        # Timer mit 10 Hz (alle 0.1 Sekunden)
        self.timer = self.create_timer(0.1, self.publish_wind)
        
        self.get_logger().info('Statischer Wind-Publisher gestartet. Sende konstanten Windvektor...')

    def publish_wind(self):
        msg = Vector3()
        # Unser kalibrierter Windvektor für den perfekten Halbwindkurs beim Start (-Y-Richtung)
        msg.x = 0.0
        msg.y = -3.0  # 3 m/s (~6 Knoten) aus Norden
        msg.z = 0.0
        
        self.wind_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = StaticWindPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
