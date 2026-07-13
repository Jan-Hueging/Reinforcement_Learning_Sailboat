from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # ===================================================================
        # THE PARAMETER BRIDGE (Übersetzer für alle Sensoren und Aktuatoren)
        # ===================================================================
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='boot_parameter_bridge',
            output='screen',
            arguments=[
                # 1. IMU (Krängung & Kompass) -> Gazebo (GZ) zu ROS 2
                '/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
                
                # 2. GPS -> Gazebo zu ROS 2
                '/GPS@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
                
                # 3. Windmesser (Scheinbarer Windvektor) -> Gazebo zu ROS 2
                '/wind_measurement@geometry_msgs/msg/Vector3[gz.msgs.Vector3d',
                
                # 4. Globaler wahrer Wind (Richtung) -> Gazebo zu ROS 2 (VRX Debug)
                '/Windrichtung@std_msgs/msg/Float64[gz.msgs.Double',
                
                # 5. Globaler wahrer Wind (Geschwindigkeit) -> Gazebo zu ROS 2 (VRX Debug)
                '/Windgeschwindigkeit@std_msgs/msg/Float64[gz.msgs.Double',
                
                # 6. Ruder-Ansteuerung (Soll-Winkel) -> ROS 2 zu Gazebo
                '/Ruderstellung_Soll@std_msgs/msg/Float64]gz.msgs.Double',
                
                # 7. Segel-Ansteuerung (Schot-Limit) -> ROS 2 zu Gazebo
                '/Segelstellung_Soll@std_msgs/msg/Float64]gz.msgs.Double',
                
                # 8. Globale Gelenkzustände (Aktuelle Winkel von Ruder und Segel) -> Gazebo zu ROS 2
                '/world/sydney_regatta/model/opti_boot/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',

                # In deinem Bridge-Launchfile als Argument hinzufügen:
                '/model/opti_boot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',

                '/wind@geometry_msgs/msg/Vector3@gz.msgs.Vector3d',

                '/model/opti_boot/set_pose@geometry_msgs/msg/Pose]gz.msgs.Pose',

                '/model/opti_boot/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.TwistWithCovariance',

                '/world/sydney_regatta/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'

            ]
        ),

        # ===================================================================
        # DER SENSOR TRANSFORMER (Dein Python-Knoten für Krängung/Kompass)
        # ===================================================================
        Node(
            package='opti_controller',
            executable='transformer',
            name='sensor_transformer',
            output='screen'
        ),
    ])
