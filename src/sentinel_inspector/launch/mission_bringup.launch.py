import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    sim_pkg = get_package_share_directory('sentinel_simulation')
    insp_pkg = get_package_share_directory('sentinel_inspector')
    nav2_pkg = get_package_share_directory('nav2_bringup')

    map_file = os.path.join(insp_pkg, 'maps', 'substation_map.yaml')
    rviz_config = os.path.join(nav2_pkg, 'rviz', 'nav2_default_view.rviz')

    return LaunchDescription([
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),

        # 1. Launch Gazebo Sim + Robot + Bridge
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(sim_pkg, 'launch', 'sim.launch.py'))
        ),

        # 2. Launch Nav2 after 4 seconds (gives Gazebo time to spawn)
        TimerAction(
            period=4.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(os.path.join(nav2_pkg, 'launch', 'bringup_launch.py')),
                    launch_arguments={'use_sim_time': 'True', 'map': map_file}.items()
                )
            ]
        ),

        # 3. Launch RViz2, Thermal Vision, and Battery Monitor after 6 seconds
        TimerAction(
            period=6.0,
            actions=[
                Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config]),
                Node(package='sentinel_inspector', executable='thermal_vision', parameters=[{'use_sim_time': True}]),
                Node(package='sentinel_inspector', executable='battery_monitor', parameters=[{'use_sim_time': True}])
            ]
        )
    ])