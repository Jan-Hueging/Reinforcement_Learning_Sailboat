import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # Paket-Pfade auflösen
    opti_controller_dir = get_package_share_directory('opti_controller')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')
    vrx_gz_dir = get_package_share_directory('vrx_gz')
    
    # Pfad zu deiner optimierten Welt-Datei (Wind muss dort auf [0, -3, 0] stehen!)
    world_path = os.path.join(vrx_gz_dir, 'worlds', 'sydney_regatta_opti.sdf')

    # Absoluter Pfad zu deiner Boot-Xacro
    boot_xacro_path = '/home/marvin/sailing_ws/src/vrx/vrx_urdf/opti_gazebo/urdf/opti_gazebo.urdf.xacro'

    # 1. Gazebo mit der Opti-Welt im Run-Modus (-r) starten
        # Gazebo OHNE '-r' starten, damit die Welt pausiert lädt
    gazebo_start = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'{world_path}'  # Das -r wurde hier entfernt!
        }.items()
    )

    # 2. XACRO ZU URDF PARSEN
    robot_description_content = Command(['xacro ', boot_xacro_path])
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(robot_description_content, value_type=str)
        }]
    )

    # 3. Boot im Ursprung spawnen 
    # WICHTIG: -Y 0.0 richtet den Bug nach Osten aus. 
    # Da der Wind aus Norden (-Y) kommt, ist das der perfekte Halbwindkurs zum Anfahren!
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
            '-R', '0.0', 
            '-P', '0.0', 
            '-Y', '0.0'  
        ]
    )

    # 4. Brücken und Transformer laden
    boot_bridges = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(opti_controller_dir, 'launch', 'boot_bridges.launch.py')
        )
    )

    # 5. DIE AUTOMATISIERTE TEST-NODE STARTEN
    # Wir nutzen eine TimerAction, um der Simulation 5 Sekunden Zeit zu geben, 
    # stabil hochzufahren und das Boot zu spawnen, bevor das Testskript loslegt.
    test_script_node = Node(
        package='opti_controller',        # Name deines ROS-Pakets
        executable='validation_test', # Name deiner ausführbaren Python-Datei
        output='screen',
        emulate_tty=True,                   # Sorgt dafür, dass get_logger().info() farbig im Terminal erscheint
    )

    wind = Node(
        package='opti_controller',        # Name deines ROS-Pakets
        executable='wind', # Name deiner ausführbaren Python-Datei
        output='screen',
        emulate_tty=True,                   # Sorgt dafür, dass get_logger().info() farbig im Terminal erscheint
        # parameters=[{'use_sim_time': True}]
    )

    reset = Node(
        package='opti_controller',        # Name deines ROS-Pakets
        executable='reset_node', # Name deiner ausführbaren Python-Datei
        output='screen',
        emulate_tty=True,                   # Sorgt dafür, dass get_logger().info() farbig im Terminal erscheint
        parameters=[{'use_sim_time': True}]
    )

    delayed_test_script = TimerAction(
        period=5.0,                        # 5 Sekunden Verzögerung
        actions=[test_script_node]
    )

    return LaunchDescription([
        gazebo_start,
        robot_state_publisher,
        boot_spawner,
        boot_bridges,
        #test_script_node,
        wind
        #delayed_test_script 
        #reset               # Startet zeitverzögert
    ])
