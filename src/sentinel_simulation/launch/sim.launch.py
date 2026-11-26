import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():
    desc_pkg = get_package_share_directory('sentinel_description')
    sim_pkg = get_package_share_directory('sentinel_simulation')
    ros_gz_pkg = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(desc_pkg, 'urdf', 'sentinel_urdf.xacro')
    world_file = os.path.join(sim_pkg, 'worlds', 'substation_world.sdf')
    bridge_config = os.path.join(sim_pkg, 'config', 'bridge.yaml')

    robot_description = Command(['xacro ', xacro_file])

    return LaunchDescription([
        # 1. Start Gazebo Sim with Substation World
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ros_gz_pkg, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': f'-r {world_file}'}.items()
        ),

        # 2. Robot State Publisher (with use_sim_time=True)
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
        ),

        # 3. Spawn Sentinel onto the green charging pad
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-topic', 'robot_description', '-name', 'sentinel', '-x', '0.0', '-y', '0.0', '-z', '0.15'],
            output='screen'
        ),

        # 4. ROS-Gazebo Topic Bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': bridge_config, 'use_sim_time': True}],
            output='screen'
        )
    ])

