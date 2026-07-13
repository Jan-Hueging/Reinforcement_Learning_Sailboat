from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Parameter Bridge (Übersetzer zwischen Gazebo und ROS 2)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_ros_bridge',
            output='screen',
            arguments=[
                '/imu/data@sensor_msgs/msg/Imu@gz.msgs.IMU',
                '/gps/data@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat',
                #'/wind_measurement@geometry_msgs/msg/Vector3d@gz.msgs.Vector3d'
            ]
        ),

        # 2. Dein Python Sensor-Transformer (Krängung & Kompass)
        Node(
            package='opti_controller',
            executable='transformer',
            name='sensor_transformer',
            output='screen'
        ),

        # 3. Dein SailLimitPlugin / Segelsteuerung (Falls als ROS-Knoten implementiert)
        # Node(
        #     package='opti_controller',
        #     executable='sail_limit_plugin_node', # Passe den Namen an dein Plugin an
        #     name='sail_controller',
        #     output='screen'
        # )
    ])
