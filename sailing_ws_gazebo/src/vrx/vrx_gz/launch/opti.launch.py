import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Performance-Hack für ältere CPUs aktivieren
    set_env = SetEnvironmentVariable(name='OPENBLAS_NUM_THREADS', value='1')

    # 2. Pfade zu Ihren Dateien auflösen
    opti_desc_dir = get_package_share_directory('opti_description')
    urdf_file = os.path.join(opti_desc_dir, 'urdf', 'optimist_complete.urdf')
    
    # Wir nutzen die Standard-Leerwelt von Gazebo, um Ihren Laptop maximal zu entlasten
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')
    
    # 3. Gazebo Server & Client starten (Hier wird eine Standardwelt geladen)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # 4. Den Optimisten in die Welt spawnen (setzen auf z=0.5, damit er ins Wasser fällt)
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', urdf_file,
            '-name', 'optimist',
            '-x', '0.0', '-y', '0.0', '-z', '0.5'
        ],
        output='screen'
    )

    # 5. Den Robot State Publisher für die Gelenke (Ruder/Segel) starten
    with open(urdf_file, 'r') as infp:
        robot_desc = infp.read()

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}]
    )

    return LaunchDescription([
        set_env,
        gazebo,
        spawn_robot,
        robot_state_publisher
    ])
