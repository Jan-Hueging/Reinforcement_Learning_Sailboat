import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # Paket-Pfade auflösen
    opti_controller_dir = get_package_share_directory('opti_controller')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')
    vrx_gz_dir = get_package_share_directory('vrx_gz')
    
    # Pfad zu deiner optimierten Welt-Datei (Nutzt deine sydney_regatta_opti.sdf)
    world_path = os.path.join(vrx_gz_dir, 'worlds', 'sydney_regatta_opti.sdf')
    
    # Falls die Datei im Quellordner deines Workspaces liegt, kannst du auch den direkten Pfad nehmen:
    # world_path = '/home/marvin/sailing_ws/src/vrx/vrx_gz/worlds/sydney_regatta_opti.sdf'

    # Absoluter Pfad zu deiner Boot-Xacro
    boot_xacro_path = '/home/marvin/sailing_ws/src/vrx/vrx_urdf/opti_gazebo/urdf/opti_gazebo.urdf.xacro'

    # 1. DEIN SCHLANKER WEG: Gazebo direkt mit der Opti-Welt starten
    # '-r' sorgt dafür, dass die Simulation sofort läuft (run)
    gazebo_start = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'-r {world_path}'
        }.items()
    )

    # 2. XACRO ZU URDF PARSEN (Live bei jedem Start)
    robot_description_content = Command(['xacro ', boot_xacro_path])
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(robot_description_content, value_type=str)
        }]
    )

    # 3. Dein Boot im Ursprung spawnen (Perfekt zum schrägen Wind ausgerichtet
    boot_spawner = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'opti_boot',
            '-x', '0.0', 
            '-y', '0.0', 
            '-z', '0.1',
            # KORREKTUR: In der aktuellen ros_gz_sim Version werden die 
            # Orientierungen oft als Großbuchstaben (X Y Z R P Y) verlangt:
            '-R', '0.0', 
            '-P', '0.0', 
            '-Y', '-0.4'  # Drehung um 45 Grad (Hier deinen Wunschwinkel eintragen!)
        ]
    )


    # 4. Deine Brücken und den Transformer dazuladen
    boot_bridges = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(opti_controller_dir, 'launch', 'boot_bridges.launch.py')
        )
    )

    return LaunchDescription([
        gazebo_start,
        robot_state_publisher,
        boot_spawner,
        boot_bridges
    ])
