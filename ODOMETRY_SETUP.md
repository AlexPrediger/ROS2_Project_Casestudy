# VESC Odometry and State Publishing

## Summary

✅ **Now we have complete odometry and state publishing!**

### What's Included:

1. **Robot State Publisher** - Publishes robot URDF and static transforms
2. **VESC to Odometry Node** - Converts VESC feedback to odometry and joint states  
3. **Joint State Publisher** - Published by `vesc_to_odom` node (no separate node needed)

## Architecture

```
VESC Motor Controller
    ↓ (sensors/core - VescStateStamped)
vesc_to_odom node
    ↓ publishes:
    ├── /odom (nav_msgs/Odometry)
    ├── /joint_states (sensor_msgs/JointState)
    └── TF: odom → base_link
    
robot_state_publisher
    ├── reads: /joint_states
    └── publishes TF: base_link → wheels, lidar, etc.
```

## Published Topics

| Topic | Type | Publisher | Description |
|-------|------|-----------|-------------|
| `/odom` | nav_msgs/Odometry | vesc_to_odom | Robot odometry (position, velocity) |
| `/joint_states` | sensor_msgs/JointState | vesc_to_odom | Wheel and steering joint positions |
| `/tf` | tf2_msgs/TFMessage | vesc_to_odom + robot_state_publisher | Complete transform tree |

## TF Tree

```
odom
 └── base_link (from vesc_to_odom)
      ├── body_link (from robot_state_publisher)
      │    ├── front_left_steer_link
      │    │    └── front_left_wheel_link
      │    ├── front_right_steer_link
      │    │    └── front_right_wheel_link
      │    ├── rear_left_wheel_link
      │    ├── rear_right_wheel_link
      │    └── laser_frame
      └── (other sensor frames...)
```

## How VESC to Odometry Works

### 1. Input Sources

The `vesc_to_odom` node subscribes to:
- **Primary**: `/sensors/core` (VescStateStamped) - Real VESC telemetry
- **Fallback**: `/commands/motor/speed` (Float64) - If VESC msgs not available
- `/steering_angle` (Float64) - Current steering angle

### 2. Odometry Computation

Uses **Ackermann steering kinematics**:

```python
# Linear velocity from rear wheels (drive wheels)
v = erpm * erpm_to_speed_gain * wheel_radius

# Angular velocity from steering geometry
if steering_angle != 0:
    turning_radius = wheelbase / tan(steering_angle)
    omega = v / turning_radius
else:
    omega = 0  # Straight motion

# Position update (Euler integration)
x += v * cos(theta) * dt
y += v * sin(theta) * dt
theta += omega * dt
```

### 3. Output

Publishes:
- **Odometry message**: Position (x, y, θ), velocity (vx, ω), covariance
- **Joint states**: Wheel positions and velocities, steering angles
- **TF transform**: odom → base_link

## Configuration

### Parameters (in vesc_to_odom_params.yaml)

```yaml
wheel_radius: 0.04           # Measure your wheel
wheelbase: 0.3               # Front-to-rear axle distance
track_width: 0.2             # Left-to-right wheel distance
erpm_to_speed_gain: 0.000216699  # Calibrate this!
```

### Calibrating ERPM Gain

The most important parameter is `erpm_to_speed_gain`:

1. **Method 1: Calculate from motor specs**
   ```
   erpm_to_speed_gain = 1.0 / (motor_poles * gear_ratio)
   ```
   - For 14-pole motor with gear ratio 4.5: `1.0 / (14 * 4.5) ≈ 0.0159`

2. **Method 2: Empirical calibration**
   ```bash
   # Drive robot forward 1 meter at constant speed
   # Measure:
   # - Distance traveled: d_actual
   # - Odometry reports: d_odom
   
   # Adjust gain:
   new_gain = old_gain * (d_actual / d_odom)
   ```

## Testing Odometry

### 1. Check TF Tree
```bash
# Install tf2_tools if needed
sudo apt install ros-${ROS_DISTRO}-tf2-tools

# View TF tree
ros2 run tf2_tools view_frames

# Check specific transform
ros2 run tf2_ros tf2_echo odom base_link
```

### 2. Monitor Odometry
```bash
# View odometry messages
ros2 topic echo /odom

# Check publish rate
ros2 topic hz /odom

# Should be ~20 Hz (matches VESC state update rate)
```

### 3. Monitor Joint States
```bash
# View joint positions
ros2 topic echo /joint_states

# Should see wheel positions incrementing as robot moves
```

### 4. Visualize in RViz
```bash
# Launch with RViz
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py use_rviz:=true

# In RViz:
# - Add Odometry display (topic: /odom)
# - Add TF display to see coordinate frames
# - Add RobotModel to see the robot
```

## Comparison: Simulation vs Real

| Component | Simulation | Real Robot |
|-----------|------------|------------|
| **Odometry Source** | Gazebo ground truth | VESC encoder feedback |
| **Accuracy** | Perfect (unless noise added) | Subject to wheel slip, calibration |
| **Joint States** | From ros2_control | From vesc_to_odom |
| **TF odom→base_link** | From Gazebo | From vesc_to_odom |

## Improving Odometry Accuracy

### 1. Add IMU Fusion
Use robot_localization to fuse odometry with IMU:

```bash
sudo apt install ros-${ROS_DISTRO}-robot-localization

# Configure robot_localization to fuse:
# - Wheel odometry (/odom)
# - IMU data (/imu/data)
# Output: Improved /odometry/filtered
```

### 2. Use AMCL for Localization
When you have a map, use AMCL (Adaptive Monte Carlo Localization):

```bash
# AMCL fuses:
# - Odometry (from wheels)
# - Lidar scans (from /scan)
# - Known map
# Output: Accurate pose in map frame
```

### 3. Visual Odometry
Add a camera and use visual odometry for better accuracy:
- ORB-SLAM2
- RTAB-Map
- OpenVSLAM

## Troubleshooting

### Odometry not publishing
```bash
# Check if node is running
ros2 node list | grep vesc_to_odom

# Check for errors
ros2 node info /vesc_to_odom
```

### TF frames missing
```bash
# List all frames
ros2 run tf2_ros tf2_echo <source> <target>

# Check if joint_states are published
ros2 topic hz /joint_states
```

### Odometry drifts quickly
- **Cause**: Incorrect `erpm_to_speed_gain`
- **Fix**: Recalibrate using the empirical method above
- **Also check**: Wheel radius measurement

### Wheels spinning in RViz but robot not moving
- **Cause**: TF tree not complete
- **Fix**: Ensure robot_state_publisher is running and receiving joint_states

### Robot moving but odometry stays at 0
- **Cause**: vesc_to_odom not receiving VESC feedback
- **Fix**: 
  - Check `/sensors/core` topic exists: `ros2 topic list`
  - If not, check if vesc_driver is running
  - Check fallback to `/commands/motor/speed`

## Files Created

1. **vesc_to_odom.py** - Main odometry computation node
   - Path: `ros2_ws/src/ackermann_vesc_adapter/ackermann_vesc_adapter/vesc_to_odom.py`
   
2. **vesc_to_odom_params.yaml** - Configuration parameters
   - Path: `ros2_ws/src/ackermann_vesc_adapter/config/vesc_to_odom_params.yaml`

3. **Updated setup.py** - Registered new node
   - Added `vesc_to_odom` entry point

4. **Updated real_vehicle.launch.py** - Integrated odometry node
   - Added vesc_to_odom_node to launch

## Next Steps

1. **Build the workspace**:
   ```bash
   cd ros2_ws
   colcon build --packages-select ackermann_vesc_adapter
   source install/setup.bash
   ```

2. **Test odometry**:
   - Launch real robot
   - Drive it around
   - Monitor odometry accuracy

3. **Calibrate parameters**:
   - Measure actual vs reported distances
   - Adjust `erpm_to_speed_gain`
   - Tune covariance values

4. **Add IMU** (optional but recommended):
   - Improves orientation estimation
   - Reduces drift in long runs
   - Better handling of wheel slip

5. **Integrate with Navigation**:
   - Use `/odom` as odometry source
   - Configure Nav2 with proper covariance
   - Tune local/global costmaps
