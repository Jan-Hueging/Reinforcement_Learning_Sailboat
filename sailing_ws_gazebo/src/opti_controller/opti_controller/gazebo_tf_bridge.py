#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from gz.msgs import Pose_V

class GazeboTFBridge(Node):
    def __init__(self):
        super().__init__('gazebo_tf_bridge')

        self.tf_broadcaster = TransformBroadcaster(self)

        self.subscription = self.create_subscription(
            Pose_V,
            '/world/sydney_regatta/dynamic_pose/info',
            self.pose_callback,
            10)

    def pose_callback(self, msg):
        for pose in msg.pose:
            name = pose.name  # e.g. "opti_boot::sail_link"
            if "::" not in name:
                continue

            model, link = name.split("::")

            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = model
            t.child_frame_id = f"{model}/{link}"

            t.transform.translation.x = pose.position.x
            t.transform.translation.y = pose.position.y
            t.transform.translation.z = pose.position.z

            t.transform.rotation = pose.orientation

            self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = GazeboTFBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()