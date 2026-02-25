"""
Nav2 launch file for autonomous navigation with the real Ackermann vehicle.
This launch file includes:
- Real vehicle hardware (VESC, lidar)
- AMCL for localization on a pre-built map
- Nav2 navigation stack
- Map server to load a saved map
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetRemap
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Get package directories
    pkg_dir = get_package_share_directory('gazebo_ackermann_steering_vehicle')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    config_dir = os.path.join(pkg_dir, 'config')
    
    # Configuration files
    nav2_params_file = os.path.join(config_dir, 'nav2_params.yaml')
    amcl_params_file = os.path.join(config_dir, 'amcl_params.yaml')
    
    # Launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time')
    
    vesc_port_arg = DeclareLaunchArgument(
        'vesc_port',
        default_value='/dev/ttyACM0',
        description='Serial port for the VESC motor controller')
    
    lidar_port_arg = DeclareLaunchArgument(
        'lidar_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for the Lidar')
    
    map_yaml_arg = DeclareLaunchArgument(
        'map',
        default_value='',
        description='Full path to map yaml file to load')
    
    autostart_arg = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the nav2 stack')
    
    use_respawn_arg = DeclareLaunchArgument(
        'use_respawn',
        default_value='false',
        description='Whether to respawn if a node crashes')
    
    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Log level')
    
    # Get launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    vesc_port = LaunchConfiguration('vesc_port')
    lidar_port = LaunchConfiguration('lidar_port')
    map_yaml_file = LaunchConfiguration('map')
    autostart = LaunchConfiguration('autostart')
    use_respawn = LaunchConfiguration('use_respawn')
    log_level = LaunchConfiguration('log_level')
    
    # Create our own temporary YAML files that include substitutions
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file
    }
    
    configured_params = RewrittenYaml(
        source_file=nav2_params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True
    )
    
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
    
    # Map server node
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[configured_params],
        arguments=['--ros-args', '--log-level', log_level]
    )
    
    # AMCL (localization) node
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[amcl_params_file],
        arguments=['--ros-args', '--log-level', log_level]
    )
    
    # Lifecycle manager for map server and AMCL
    lifecycle_manager_localization = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'node_names': ['map_server', 'amcl']
        }]
    )
    
    # Nav2 bringup (includes all navigation nodes)
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'params_file': nav2_params_file,
            'use_respawn': use_respawn,
        }.items()
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        vesc_port_arg,
        lidar_port_arg,
        map_yaml_arg,
        autostart_arg,
        use_respawn_arg,
        log_level_arg,
        
        # Launch the real vehicle (hardware + sensors)
        real_vehicle_launch,
        
        # Launch map server and AMCL
        map_server_node,
        amcl_node,
        lifecycle_manager_localization,
        
        # Launch Nav2 navigation stack
        nav2_bringup_launch,
    ])
