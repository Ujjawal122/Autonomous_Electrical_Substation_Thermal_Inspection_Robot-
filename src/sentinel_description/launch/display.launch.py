import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('sentinel_description')
    xacro_file = os.path.join(pkg_dir, 'urdf', 'sentinel_urdf.xacro')
    robot_description = Command(['xacro ', xacro_file])

    rviz_config = os.path.join(pkg_dir, 'rviz', 'view_robot.rviz')
    rviz_args = ['-d', rviz_config] if os.path.exists(rviz_config) else []

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=rviz_args,
            additional_env={'QT_QPA_PLATFORM': 'xcb'}
        )
    ])