# Real Robot Setup Guide

This guide explains how to transition from the Gazebo simulation to your real Ackermann steering robot with VESC motors and Lidar.

## Hardware Requirements

1. **VESC Motor Controller** - Connected via USB/Serial (typically `/dev/ttyACM0`)
2. **Lidar Sensor** - One of the following:
   - RPLidar A1/A2/A3 (most common)
   - LD06/LD19 Lidar
   - SICK TiM series
   - Or any ROS2-compatible 2D lidar
3. **Onboard Computer** - Raspberry Pi, Jetson, or similar running ROS2
4. **Ackermann Steering Vehicle** - 4-wheel robot with front steering

## Software Requirements

Make sure you have the following ROS2 packages installed:

```bash
# Core packages (should already be installed)
sudo apt install ros-${ROS_DISTRO}-robot-state-publisher
sudo apt install ros-${ROS_DISTRO}-joint-state-publisher

# For RPLidar (choose based on your lidar model)
sudo apt install ros-${ROS_DISTRO}-rplidar-ros

# Alternative: For LD06/LD19 Lidar
# git clone into your workspace: https://github.com/linorobot/ldlidar

# Alternative: For SICK Lidar
# sudo apt install ros-${ROS_DISTRO}-sick-scan

# VESC driver (if not already in your workspace)
# This should already be present in your ros2_ws/src/vesc/vesc_driver
```

## Configuration Steps

### 1. Identify Your Hardware Ports

Find the serial port for your VESC and Lidar:

```bash
# List all USB devices
ls -l /dev/tty*

# For VESC (usually):
# /dev/ttyACM0 or /dev/ttyACM1

# For Lidar (usually):
# /dev/ttyUSB0 or /dev/ttyUSB1 or /dev/rplidar

# Set up udev rules for consistent naming (recommended)
# Create /etc/udev/rules.d/99-robot.rules with:
# SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", SYMLINK+="vesc"
# SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar"

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2. Configure Your Robot Parameters

Edit the configuration file to match your robot's dimensions:

```bash
cd ~/ros2_ws/src/gazebo_ackermann_steering_vehicle/config
nano real_vehicle_params.yaml
```

Important parameters to adjust:
- `body_length`, `body_width`, `body_height` - Measure your robot
- `wheel_radius` - Measure your wheel diameter
- `max_steering_angle` - Test your maximum steering angle
- `lidar_*` parameters - Based on your lidar specifications
- `vesc_to_erpm_gain` - Calibrate based on your motor and gearing

### 3. Configure Lidar in Launch File

Edit the launch file to match your lidar model:

```bash
cd ~/ros2_ws/src/gazebo_ackermann_steering_vehicle/launch
nano real_vehicle.launch.py
```

The launch file includes examples for:
- **RPLidar** (default, most common)
- **LD06 Lidar** (commented out)
- **SICK TiM** (commented out)

Uncomment and configure the section for your lidar model.

### 4. Tune the Ackermann-to-VESC Adapter

The `ackermann_to_vesc.py` node converts velocity and steering commands to VESC motor/servo commands.

Parameters to tune (in `ackermann_to_vesc.py`):
```python
self.max_vehicle_speed = 4.0        # Maximum speed in m/s
self.max_erpm = 23250.0             # Maximum ERPM for your VESC
self.max_steer = 0.6                 # Maximum steering angle in radians
self.servo_center = 0.50             # Servo center position (0.0 - 1.0)
self.servo_range = 0.35              # Servo range from center
```

## Building and Running

### 1. Build the Workspace

```bash
cd ~/ros2_ws
colcon build --packages-select gazebo_ackermann_steering_vehicle ackermann_vesc_adapter
source install/setup.bash
```

### 2. Launch the Real Robot

```bash
# Basic launch with default ports
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py

# With custom ports
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py \
    vesc_port:=/dev/ttyACM0 \
    lidar_port:=/dev/ttyUSB0

# With RViz for visualization
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py use_rviz:=true
```

### 3. Test the Robot

In a new terminal, test basic movement:

```bash
# Test velocity command (forward)
ros2 topic pub /velocity std_msgs/Float64 "data: 1.0"

# Test steering (turn left)
ros2 topic pub /steering_angle std_msgs/Float64 "data: 0.3"

# Stop
ros2 topic pub /velocity std_msgs/Float64 "data: 0.0"
```

Check that you're receiving lidar data:

```bash
ros2 topic echo /scan
ros2 topic hz /scan
```

### 4. Monitor VESC Commands

Check what commands are being sent to the VESC:

```bash
# Motor speed (ERPM)
ros2 topic echo /commands/motor/speed

# Servo position
ros2 topic echo /commands/servo/position
```

## Integration with Navigation

To use your real robot with ROS2 Navigation Stack:

1. **Create a map** using SLAM:
```bash
# Install SLAM Toolbox
sudo apt install ros-${ROS_DISTRO}-slam-toolbox

# Run SLAM while teleoperating your robot
ros2 launch slam_toolbox online_async_launch.py
```

2. **Use Navigation2**:
```bash
# Install Nav2
sudo apt install ros-${ROS_DISTRO}-navigation2 ros-${ROS_DISTRO}-nav2-bringup

# Launch navigation with your saved map
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=false
```

## Troubleshooting

### VESC Not Responding
- Check serial port permissions: `sudo chmod 666 /dev/ttyACM0`
- Verify VESC is powered and connected
- Check baud rate (usually 115200)
- Use VESC Tool to test motor connection

### Lidar Not Publishing
- Check serial port: `ls -l /dev/ttyUSB*`
- Verify baudrate matches your lidar (115200 for RPLidar A1/A2, 230400 for A3)
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`
- Test with lidar manufacturer's tool

### Robot Not Moving
- Check /velocity and /steering_angle topics are being published
- Verify ackermann_to_vesc node is running: `ros2 node list`
- Monitor VESC commands: `ros2 topic echo /commands/motor/speed`
- Check safety timeout in ackermann_to_vesc.py (default 0.5s)

### TF Transform Errors
- Verify robot_state_publisher is running: `ros2 node list`
- Check TF tree: `ros2 run tf2_tools view_frames`
- Ensure base_link and laser_frame are in the TF tree

## Safety Notes

⚠️ **Important Safety Considerations:**

1. **Test in a safe area** - Start with low speeds in an open space
2. **Emergency stop** - Have a way to quickly stop the robot (kill switch)
3. **Command timeout** - The ackermann_to_vesc node has a 0.5s timeout that stops the robot if no commands are received
4. **Speed limits** - Start with low `max_vehicle_speed` and increase gradually
5. **Steering limits** - Verify `max_steering_angle` to prevent mechanical damage
6. **Battery monitoring** - Monitor VESC for battery voltage
7. **Wire management** - Ensure cables won't get caught in wheels

## Next Steps

- Calibrate odometry for accurate position estimation
- Tune PID controllers for smooth motion
- Set up sensor fusion (IMU + wheel odometry + lidar)
- Configure Nav2 parameters for your robot's dynamics
- Implement obstacle avoidance
- Add teleoperation interface (joystick or keyboard)

## Reference Topics

Key ROS2 topics for your robot:

| Topic | Type | Description |
|-------|------|-------------|
| `/velocity` | std_msgs/Float64 | Target velocity (m/s) |
| `/steering_angle` | std_msgs/Float64 | Target steering angle (rad) |
| `/commands/motor/speed` | std_msgs/Float64 | VESC motor speed (ERPM) |
| `/commands/servo/position` | std_msgs/Float64 | Servo position (0.0-1.0) |
| `/scan` | sensor_msgs/LaserScan | Lidar scan data |
| `/robot_description` | std_msgs/String | Robot URDF |
| `/tf` | tf2_msgs/TFMessage | Transform tree |

## Additional Resources

- [VESC Project Documentation](https://vesc-project.com/)
- [ROS2 Navigation2](https://navigation.ros.org/)
- [RPLidar ROS2 Package](https://github.com/Slamtec/rplidar_ros)
- [Ackermann Steering](https://en.wikipedia.org/wiki/Ackermann_steering_geometry)
