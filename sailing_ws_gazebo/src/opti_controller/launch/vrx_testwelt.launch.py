import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    opti_controller_dir = get_package_share_directory('opti_controller')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')
    opti_description_dir = get_package_share_directory('opti_description')
    
    boot_xacro_path = os.path.join(opti_description_dir, 'urdf', 'optimist_complete.urdf.xacro')
    world_path = os.path.join(opti_controller_dir, 'worlds', 'test_world.world')

    # Wir injizieren die VRX-Bibliotheken direkt, damit das Wind- und Wellenplugin geladen werden kann
    vrx_plugin_path = '/home/marvin/sailing_ws/install/vrx_gz/lib'
    set_plugin_path = SetEnvironmentVariable(name='GZ_SIM_SYSTEM_PLUGIN_PATH', value=vrx_plugin_path)

    # 1. Reines Gazebo Sim mit unserer leichten Performance-Welt starten
    gazebo_start = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_path}'}.items()
    )

    # 2. Roboter-Zustand parsen
    robot_description_content = Command(['xacro ', boot_xacro_path])
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(robot_description_content, value_type=str)
        }]
    )

    # 3. Dein Boot spawnen
    boot_spawner = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'opti_boot',
            '-x', '0.0', '-y', '0.0', '-z', '0.05'
        ]
    )

    # 4. ROS-Bridges und Python-Transformer zünden
    ros_software = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(opti_controller_dir, 'launch', 'boot.launch.py')
        )
    )

    return LaunchDescription([
        set_plugin_path,
        gazebo_start,
        robot_state_publisher,
        boot_spawner,
        ros_software
    ])
