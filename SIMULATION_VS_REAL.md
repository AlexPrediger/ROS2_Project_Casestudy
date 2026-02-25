# Simulation vs Real Robot Comparison

This document compares the simulation setup with the real robot setup to help you understand the differences and how to transition between them.

## Overview

| Aspect | Simulation (Gazebo) | Real Robot |
|--------|---------------------|------------|
| **Physics** | Simulated by Gazebo | Real-world physics |
| **Motors** | Gazebo controllers | VESC motor controllers |
| **Sensors** | Simulated lidar | Physical lidar (RPLidar, LD06, etc.) |
| **Time** | Simulation time (`use_sim_time: true`) | Real-time (`use_sim_time: false`) |
| **Safety** | No physical risks | Requires safety precautions |
| **Testing Speed** | Can be faster than real-time | Real-time only |

## Launch Files

### Simulation
```bash
# Launch simulation with Gazebo
ros2 launch gazebo_ackermann_steering_vehicle vehicle.launch.py

# This starts:
# - Gazebo simulator
# - Robot State Publisher
# - Gazebo-ROS Bridge
# - Joint State Broadcaster
# - Velocity/Position Controllers
# - Vehicle Controller
```

**File**: `ros2_ws/src/gazebo_ackermann_steering_vehicle/launch/vehicle.launch.py`

### Real Robot
```bash
# Launch real robot hardware
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py \
    vesc_port:=/dev/ttyACM0 \
    lidar_port:=/dev/ttyUSB0

# This starts:
# - Robot State Publisher (no sim time)
# - VESC Driver Node
# - Ackermann-to-VESC Adapter
# - Lidar Driver
```

**File**: `ros2_ws/src/gazebo_ackermann_steering_vehicle/launch/real_vehicle.launch.py`

## Robot Description (URDF)

### Simulation URDF
- **File**: `model/vehicle.xacro`
- **Features**:
  - Detailed visual and collision meshes
  - Gazebo-specific plugins (ros_gz_sim)
  - Simulated sensors (lidar, camera)
  - ros2_control with Gazebo integration
  - Inertia and mass properties for physics simulation

### Real Robot URDF
- **File**: `model/real_vehicle.xacro`
- **Features**:
  - Simplified visual representation
  - No Gazebo plugins
  - Physical sensor frames (lidar)
  - Static transforms for localization
  - Lighter (only used for visualization and TF)

## Control Architecture

### Simulation Control Flow
```
Navigation/Teleop
    ↓
/velocity & /steering_angle topics
    ↓
Vehicle Controller Node
    ↓
ros2_control (Gazebo)
    ↓
Simulated Motors
```

### Real Robot Control Flow
```
Navigation/Teleop
    ↓
/velocity & /steering_angle topics
    ↓
Ackermann-to-VESC Adapter
    ↓
/commands/motor/speed & /commands/servo/position
    ↓
VESC Driver Node
    ↓
Physical VESC Motors
```

## Topic Differences

### Simulation Topics
```bash
# Control inputs (same for both)
/velocity (std_msgs/Float64)
/steering_angle (std_msgs/Float64)

# Gazebo-specific topics
/joint_states (sensor_msgs/JointState)
/world/empty/model/ackermann_steering_vehicle/...

# Simulated sensor
/scan (sensor_msgs/LaserScan) - from Gazebo plugin
```

### Real Robot Topics
```bash
# Control inputs (same for both)
/velocity (std_msgs/Float64)
/steering_angle (std_msgs/Float64)

# VESC-specific topics
/commands/motor/speed (std_msgs/Float64)
/commands/servo/position (std_msgs/Float64)
/sensors/core (vesc_msgs/VescStateStamped) - VESC telemetry

# Physical sensor
/scan (sensor_msgs/LaserScan) - from real lidar
```

## Configuration Files

### Simulation Config
- **File**: `config/parameters.yaml`
- **Purpose**: Vehicle dimensions, controller gains, sensor specs
- **Used by**: Gazebo, controllers, vehicle controller node

### Real Robot Config
- **File**: `config/real_vehicle_params.yaml`
- **Purpose**: Physical dimensions, VESC parameters, safety limits
- **Additional parameters**:
  - VESC conversion factors (ERPM, servo position)
  - Safety timeouts
  - Acceleration limits
  - Real lidar specifications

## Key Differences in Behavior

### 1. Timing
- **Simulation**: Uses simulation time which can be paused, slowed down, or sped up
- **Real Robot**: Always runs in real-time, no pausing

### 2. Safety
- **Simulation**: No physical consequences, can test extreme scenarios
- **Real Robot**: 
  - Requires commanded timeout (0.5s default in ackermann_to_vesc)
  - Need emergency stop capability
  - Should start testing at low speeds

### 3. Sensor Noise
- **Simulation**: Can add configurable noise to sensors
- **Real Robot**: Real sensor noise, need proper filtering

### 4. Odometry
- **Simulation**: Perfect odometry from Gazebo (unless noise added)
- **Real Robot**: Need to implement odometry from:
  - VESC motor encoders
  - IMU integration
  - Wheel odometry calculations

### 5. Calibration
- **Simulation**: Parameters are exact as specified
- **Real Robot**: Requires calibration:
  - VESC speed to velocity conversion
  - Servo position to steering angle mapping
  - Lidar mounting offset and orientation
  - Maximum safe speeds and accelerations

## Sensor Integration

### Lidar

#### Simulation
```xml
<!-- In vehicle.xacro, Gazebo lidar plugin -->
<gazebo reference="lidar_link">
  <sensor name="lidar" type="gpu_lidar">
    <update_rate>10</update_rate>
    <lidar>
      <scan>
        <horizontal>
          <samples>720</samples>
          <resolution>1.0</resolution>
          <min_angle>-3.14159</min_angle>
          <max_angle>3.14159</max_angle>
        </horizontal>
      </scan>
      <range>
        <min>0.1</min>
        <max>30.0</max>
      </range>
    </lidar>
  </sensor>
</gazebo>
```

#### Real Robot
```python
# In real_vehicle.launch.py, physical lidar driver
lidar_node = Node(
    package='rplidar_ros',
    executable='rplidar_composition',
    parameters=[{
        'serial_port': '/dev/ttyUSB0',
        'frame_id': 'laser_frame',
        # ... other params
    }]
)
```

## Transitioning from Simulation to Real Robot

### 1. Test in Simulation First
- Develop and test all algorithms in simulation
- Tune parameters and verify behavior
- Test edge cases and failure modes

### 2. Prepare Hardware
- Assemble robot with VESC and lidar
- Install and test drivers individually
- Set up proper serial port permissions

### 3. Initial Real Robot Tests
- Start with very low speeds (0.5 m/s max)
- Test motor response without full vehicle
- Verify lidar data quality
- Test steering limits

### 4. Calibration
- Measure actual robot dimensions
- Calibrate VESC speed gains
- Calibrate steering servo range
- Tune acceleration limits

### 5. Gradual Integration
- Test basic teleoperation first
- Verify sensor data quality
- Implement proper odometry
- Finally integrate with navigation

### 6. Safety Checklist
- [ ] Emergency stop button accessible
- [ ] Command timeout implemented and tested
- [ ] Speed limits appropriately set
- [ ] Clear testing area with no obstacles
- [ ] Steering limits prevent mechanical damage
- [ ] Battery voltage monitoring active
- [ ] All cables secured and clear of wheels

## Common Issues and Solutions

### Issue: Robot doesn't move when given commands
**Simulation**: Check if controllers are loaded and active
```bash
ros2 control list_controllers
```

**Real Robot**: 
- Verify VESC is connected and configured
- Check ackermann_to_vesc node is running
- Monitor VESC commands being sent
- Ensure VESC has power and is not in fault state

### Issue: Sensor data not available
**Simulation**: Check if Gazebo plugins are properly configured

**Real Robot**:
- Check serial port permissions
- Verify sensor is powered
- Test sensor with manufacturer's tools
- Check ROS2 topic is being published

### Issue: Poor localization/navigation
**Simulation**: Usually not an issue unless noise is configured

**Real Robot**:
- Implement proper odometry fusion
- Calibrate sensor mounting positions
- Use AMCL or similar for localization
- Tune navigation parameters for real dynamics

## Performance Considerations

### Simulation
- CPU-intensive (Gazebo physics + rendering)
- Can run multiple instances for testing
- Deterministic (same initial conditions → same results)

### Real Robot  
- Lower computational load (no physics simulation)
- One robot at a time
- Non-deterministic (real-world variability)
- Must handle real-time constraints

## Additional Notes

### Advantages of Simulation
- Safe testing environment
- Rapid iteration
- Easy to modify environment
- No hardware wear and tear
- Can simulate extreme conditions

### Advantages of Real Robot
- Real-world performance validation
- Actual sensor characteristics
- True dynamics and non-linearities
- Real-time constraints
- Practical deployment experience

### Best Practice: Hybrid Approach
1. Develop in simulation
2. Validate key features on real hardware
3. Refine based on real-world performance
4. Regression test in simulation
5. Deploy on real robot with confidence
