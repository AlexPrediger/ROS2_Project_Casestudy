# Quick Start: Real Robot with VESC and Lidar

## 🚀 Quick Launch

```bash
# Option 1: Use the convenient script
./launch_real_robot.sh

# Option 2: Launch manually with custom ports
cd ros2_ws
source install/setup.bash
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py \
    vesc_port:=/dev/ttyACM0 \
    lidar_port:=/dev/ttyUSB0
```

## 🎮 Control Your Robot

### Keyboard Control
```bash
# In a new terminal
cd ros2_ws
source install/setup.bash
ros2 run ackermann_teleop keyboard_teleop

# Controls:
# w/s - increase/decrease speed
# a/d - turn left/right
# space - emergency stop
# q - quit
```

### Manual Commands
```bash
# Set velocity (m/s)
ros2 topic pub /velocity std_msgs/Float64 "data: 1.0"

# Set steering (radians, positive = left)
ros2 topic pub /steering_angle std_msgs/Float64 "data: 0.3"

# Stop
ros2 topic pub /velocity std_msgs/Float64 "data: 0.0"
```

## 📊 Monitor Your Robot

```bash
# Check all nodes are running
ros2 node list

# Monitor lidar data
ros2 topic echo /scan
ros2 topic hz /scan

# Monitor VESC commands
ros2 topic echo /commands/motor/speed
ros2 topic echo /commands/servo/position

# View TF tree
ros2 run tf2_tools view_frames
```

## ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| `ros2_ws/src/gazebo_ackermann_steering_vehicle/launch/real_vehicle.launch.py` | Main launch file |
| `ros2_ws/src/gazebo_ackermann_steering_vehicle/config/real_vehicle_params.yaml` | Robot dimensions and parameters |
| `ros2_ws/src/gazebo_ackermann_steering_vehicle/model/real_vehicle.xacro` | Robot URDF description |
| `ros2_ws/src/ackermann_vesc_adapter/ackermann_vesc_adapter/ackermann_to_vesc.py` | VESC control adapter |

## 🔧 Before First Run

1. **Check ports**:
   ```bash
   ls -l /dev/tty* | grep -E "ACM|USB"
   ```

2. **Set permissions**:
   ```bash
   sudo chmod 666 /dev/ttyACM0   # VESC
   sudo chmod 666 /dev/ttyUSB0   # Lidar
   ```

3. **Configure your lidar type** in `real_vehicle.launch.py`:
   - RPLidar (default, most common)
   - LD06/LD19 (uncomment appropriate section)
   - SICK TiM (uncomment appropriate section)

4. **Tune parameters** in `real_vehicle_params.yaml`:
   - Measure your robot dimensions
   - Adjust max speeds for safety
   - Configure VESC conversion factors

5. **Build workspace**:
   ```bash
   cd ros2_ws
   colcon build --packages-select gazebo_ackermann_steering_vehicle ackermann_vesc_adapter
   source install/setup.bash
   ```

## 🛡️ Safety First!

⚠️ **Before running on real hardware**:
- [ ] Test in open, clear area
- [ ] Start with LOW speeds (0.5 m/s)
- [ ] Have emergency stop ready
- [ ] Check battery level
- [ ] Verify steering limits
- [ ] Keep cables away from wheels

## 🐛 Troubleshooting

### Robot doesn't move
- Check VESC is powered and connected
- Verify `ackermann_to_vesc` node is running
- Monitor topics: `ros2 topic list`

### Lidar not working
- Check port: `ls -l /dev/ttyUSB*`
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`
- Verify driver is correct for your lidar model

### Permission errors
```bash
# For VESC
sudo usermod -a -G dialout $USER
# For Lidar
sudo usermod -a -G dialout $USER
# Then logout and login again
```

## 📚 Full Documentation

- **Setup Guide**: `REAL_ROBOT_SETUP.md` - Complete setup instructions
- **Comparison**: `SIMULATION_VS_REAL.md` - Simulation vs real robot differences
- **Main README**: `README.md` - Project overview

## 📞 Key ROS2 Topics

| Topic | Type | Purpose |
|-------|------|---------|
| `/velocity` | Float64 | Target speed (m/s) |
| `/steering_angle` | Float64 | Steering angle (rad) |
| `/scan` | LaserScan | Lidar data |
| `/commands/motor/speed` | Float64 | VESC motor speed |
| `/commands/servo/position` | Float64 | Steering servo |

## 🎯 Next Steps

1. **Test basic movement**: Use keyboard teleop to verify robot responds
2. **Check sensors**: Verify lidar is publishing scan data
3. **Calibrate**: Fine-tune VESC parameters and dimensions
4. **Map your space**: Use SLAM to create a map
5. **Navigate**: Integrate with Nav2 for autonomous navigation

---

**Need help?** Check the detailed documentation in `REAL_ROBOT_SETUP.md`
