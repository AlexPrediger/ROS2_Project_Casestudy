"""
Launch file for real Ackermann vehicle with VESC motors and Lidar.
This replaces the Gazebo simulation with real hardware interfaces.
"""

import os
import xacro
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node


def load_robot_description(robot_description_path, vehicle_params_path):
    """
    Loads the robot description from a Xacro file, using parameters from a YAML file.

    @param robot_description_path: Path to the robot's Xacro file.
    @param vehicle_params_path: Path to the YAML file containing the vehicle parameters.
    @return: A string containing the robot's URDF XML description.
    """
    # Load parameters from YAML file
    with open(vehicle_params_path, 'r') as file:
        vehicle_params = yaml.safe_load(file)['/**']['ros__parameters']

    # Process the Xacro file to generate the URDF representation of the robot
    robot_description = xacro.process_file(
        robot_description_path,
        mappings={key: str(value) for key, value in vehicle_params.items()})

    return robot_description.toxml()


def generate_launch_description():
    # Define launch arguments
    lidar_port_arg = DeclareLaunchArgument(
        'lidar_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for the Lidar (e.g., /dev/ttyUSB0 or /dev/rplidar)')
    
    vesc_port_arg = DeclareLaunchArgument(
        'vesc_port',
        default_value='/dev/ttyACM0',
        description='Serial port for the VESC motor controller')
    
    lidar_frame_arg = DeclareLaunchArgument(
        'lidar_frame',
        default_value='laser_frame',
        description='Frame ID for the lidar')
    
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz for visualization')

    # Retrieve launch configurations
    lidar_port = LaunchConfiguration('lidar_port')
    vesc_port = LaunchConfiguration('vesc_port')
    lidar_frame = LaunchConfiguration('lidar_frame')
    use_rviz = LaunchConfiguration('use_rviz')

    # Define the package name
    package_name = "gazebo_ackermann_steering_vehicle"
    package_path = get_package_share_directory(package_name)

    # Set paths to model and configuration files
    robot_description_path = os.path.join(package_path, 'model',
                                          'real_vehicle.xacro')
    
    vehicle_params_path = os.path.join(package_path, 'config',
                                       'real_vehicle_params.yaml')

    # Load URDF for the real robot (simplified, no Gazebo plugins)
    robot_description = load_robot_description(robot_description_path,
                                               vehicle_params_path)

    # Robot state publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': False  # Real robot doesn't use sim time
        }],
        output='screen'
    )

    # Ackermann to VESC adapter node
    # This converts /velocity and /steering_angle to VESC commands
    ackermann_vesc_adapter_node = Node(
        package='ackermann_vesc_adapter',
        executable='ackermann_to_vesc',
        name='ackermann_to_vesc',
        output='screen'
    )

    # VESC to Odometry node
    # Converts VESC feedback to odometry and joint states
    vesc_to_odom_params_path = os.path.join(
        get_package_share_directory('ackermann_vesc_adapter'),
        'config', 'vesc_to_odom_params.yaml'
    )
    
    vesc_to_odom_node = Node(
        package='ackermann_vesc_adapter',
        executable='vesc_to_odom',
        name='vesc_to_odom',
        parameters=[vehicle_params_path],  # Uses same vehicle params as simulation
        output='screen'
    )

    # VESC driver node (if you have the vesc_driver package installed)
    # Uncomment and configure if available
    vesc_driver_node = Node(
        package='vesc_driver',
        executable='vesc_driver_node',
        name='vesc_driver_node',
        parameters=[{
            'port': vesc_port,
            'duty_cycle_min': -0.3,
            'duty_cycle_max': 0.3,
            'current_min': -10.0,
            'current_max': 10.0,
            'brake_min': 0.0,
            'brake_max': 10.0,
            'speed_min': -5000.0,
            'speed_max': 5000.0,
            'position_min': 0.0,
            'position_max': 1.0,
            'servo_min': 0.0,
            'servo_max': 1.0,
        }],
        output='screen'
    )

    # Lidar node - RPLidar example (adjust based on your actual lidar)
    # For RPLidar A1/A2:
    lidar_node = Node(
        package='rplidar_ros',
        executable='rplidar_composition',
        name='rplidar_node',
        parameters=[{
            'serial_port': lidar_port,
            'serial_baudrate': 115200,
            'frame_id': lidar_frame,
            'inverted': False,
            'angle_compensate': True,
        }],
        output='screen'
    )
    
    # Alternative: For LD06 Lidar, use:
    # lidar_node = Node(
    #     package='ldlidar',
    #     executable='ldlidar',
    #     name='ldlidar_node',
    #     parameters=[{
    #         'serial_port': lidar_port,
    #         'topic_name': 'scan',
    #         'lidar_frame': lidar_frame,
    #         'range_threshold': 0.005,
    #     }],
    #     output='screen'
    # )
    
    # Alternative: For SICK Tim lidar:
    # lidar_node = Node(
    #     package='sick_scan',
    #     executable='sick_generic_caller',
    #     name='sick_tim_node',
    #     parameters=[{
    #         'scanner_type': 'sick_tim_5xx',
    #         'hostname': '192.168.0.1',
    #         'port': '2112',
    #         'frame_id': lidar_frame,
    #     }],
    #     output='screen'
    # )

    # Optional: RViz for visualization
    rviz_config_path = os.path.join(package_path, 'config', 'real_vehicle.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        condition=IfCondition(use_rviz),
        output='screen'
    )

    # Optional: Vehicle controller (if you have custom control logic)
    # vehicle_controller_node = Node(
    #     package='gazebo_ackermann_steering_vehicle',
    #     executable='vehicle_controller',
    #     parameters=[vehicle_params_path],
    #     output='screen'
    # )

    # Create the launch description
    launch_description = LaunchDescription([
        lidar_port_arg,
        vesc_port_arg,
        lidar_frame_arg,
        use_rviz_arg,
        robot_state_publisher_node,
        ackermann_vesc_adapter_node,
        vesc_to_odom_node,
        vesc_driver_node,  # Comment out if vesc_driver not available
        lidar_node,        # Modify based on your lidar type
        rviz_node,         # Launches only if use_rviz:=true
    ])

    return launch_description
