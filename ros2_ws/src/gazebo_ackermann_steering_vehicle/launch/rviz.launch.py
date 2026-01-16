import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    
    pkg_name = 'gazebo_ackermann_steering_vehicle'
    pkg_dir = get_package_share_directory(pkg_name)
    
    # Path to RViz config
    rviz_config_file = os.path.join(pkg_dir, 'rviz', 'vehicle.rviz')
    
    # Launch argument
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )
    
    # RViz node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    return LaunchDescription([
        declare_use_sim_time,
        rviz_node
    ])