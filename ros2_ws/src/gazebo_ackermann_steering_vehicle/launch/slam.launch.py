"""
SLAM Toolbox launch file for mapping with the real Ackermann vehicle.
Use this to create a map of your environment by driving the robot around.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # Get package directories
    pkg_dir = get_package_share_directory('gazebo_ackermann_steering_vehicle')
    config_dir = os.path.join(pkg_dir, 'config')
    
    # SLAM Toolbox parameters
    slam_params_file = os.path.join(config_dir, 'slam_toolbox_params.yaml')
    
    # Launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time for SLAM')
    
    vesc_port_arg = DeclareLaunchArgument(
        'vesc_port',
        default_value='/dev/ttyACM0',
        description='Serial port for the VESC motor controller')
    
    lidar_port_arg = DeclareLaunchArgument(
        'lidar_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for the Lidar')
    
    autostart_arg = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically start SLAM')
    
    # Get launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    vesc_port = LaunchConfiguration('vesc_port')
    lidar_port = LaunchConfiguration('lidar_port')
    autostart = LaunchConfiguration('autostart')
    
    # Include the real vehicle launch file (robot hardware + sensors)
    real_vehicle_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'real_vehicle.launch.py')
        ),
        launch_arguments={
            'vesc_port': vesc_port,
            'lidar_port': lidar_port,
        }.items()
    )
    
    # SLAM Toolbox Node (Online Async mode for real-time mapping)
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {
                'use_sim_time': use_sim_time,
            }
        ],
        remappings=[
            ('/scan', '/scan'),  # Use the lidar scan topic
        ]
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        vesc_port_arg,
        lidar_port_arg,
        autostart_arg,
        
        # Launch the real vehicle (hardware + sensors)
        real_vehicle_launch,
        
        # Launch SLAM Toolbox
        slam_toolbox_node,
    ])
