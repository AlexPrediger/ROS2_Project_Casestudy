# SLAM and Nav2 Navigation Setup Guide

This guide walks you through setting up SLAM (mapping) and Nav2 (autonomous navigation) for your Ackermann steering robot.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Install Required Packages](#install-required-packages)
3. [Phase 1: Create a Map with SLAM](#phase-1-create-a-map-with-slam)
4. [Phase 2: Navigate with Nav2](#phase-2-navigate-with-nav2)
5. [Troubleshooting](#troubleshooting)
6. [Tuning Tips](#tuning-tips)

---

## Prerequisites

✅ Your robot must have:
- Working VESC motor controller
- Functional lidar sensor
- Odometry publishing on `/odom` topic
- TF tree: `map` → `odom` → `base_link` → `laser_frame`

Check that your hardware is working:
```bash
# Terminal 1: Launch the robot
cd ~/ros2_ws
source install/setup.bash
ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py

# Terminal 2: Check topics
ros2 topic list
# Should see: /odom, /scan, /velocity, /steering_angle

# Terminal 3: Check TF tree
ros2 run tf2_tools view_frames
# Open frames.pdf to verify TF connections
```

---

## Install Required Packages

Install SLAM Toolbox and Nav2:

```bash
# Update package list
sudo apt update

# Install SLAM Toolbox for mapping
sudo apt install ros-${ROS_DISTRO}-slam-toolbox

# Install Nav2 for autonomous navigation
sudo apt install ros-${ROS_DISTRO}-navigation2 ros-${ROS_DISTRO}-nav2-bringup

# Verify installations
ros2 pkg list | grep slam_toolbox
ros2 pkg list | grep nav2
```

---

## Phase 1: Create a Map with SLAM

### Step 1: Build Your Workspace

```bash
cd ~/ros2_ws
colcon build --packages-select gazebo_ackermann_steering_vehicle
source install/setup.bash
```

### Step 2: Launch SLAM

```bash
# Launch SLAM (includes robot hardware + SLAM Toolbox)
ros2 launch gazebo_ackermann_steering_vehicle slam.launch.py \
    vesc_port:=/dev/ttyACM0 \
    lidar_port:=/dev/ttyUSB0
```

**What this does:**
- Starts your robot hardware (VESC + lidar)
- Launches SLAM Toolbox for real-time mapping
- Publishes TF: `map` → `odom` → `base_link`

### Step 3: Visualize with RViz

```bash
# In a new terminal
ros2 launch gazebo_ackermann_steering_vehicle rviz.launch.py use_sim_time:=false
```

**In RViz, add these displays:**
1. **Map** → Topic: `/map`
2. **LaserScan** → Topic: `/scan`
3. **RobotModel** → Description Topic: `/robot_description`
4. **TF** → Show all frames

### Step 4: Drive Around to Build the Map

```bash
# In a new terminal - teleop the robot
ros2 run ackermann_teleop teleop_node
```

**Mapping tips:**
- Drive slowly and smoothly
- Cover the entire area you want to map
- Revisit starting point for loop closure
- Avoid rapid turns or wheel slip
- Watch RViz to see the map being built

### Step 5: Save Your Map

Once you're happy with the map:

```bash
# Save map to current directory
ros2 run nav2_map_server map_saver_cli -f my_robot_map

# Or save to specific location
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_robot_map
```

**This creates two files:**
- `my_robot_map.yaml` - Map metadata
- `my_robot_map.pgm` - Map image

**Important:** Note the full path to the `.yaml` file - you'll need it for navigation!

---

## Phase 2: Navigate with Nav2

### Step 1: Launch Nav2 with Your Map

```bash
cd ~/ros2_ws
source install/setup.bash

# Launch Nav2 (replace with your map path)
ros2 launch gazebo_ackermann_steering_vehicle navigation.launch.py \
    vesc_port:=/dev/ttyACM0 \
    lidar_port:=/dev/ttyUSB0 \
    map:=/full/path/to/my_robot_map.yaml
```

**Example:**
```bash
ros2 launch gazebo_ackermann_steering_vehicle navigation.launch.py \
    vesc_port:=/dev/ttyACM0 \
    lidar_port:=/dev/ttyUSB0 \
    map:=/home/user/maps/my_robot_map.yaml
```

### Step 2: Visualize with RViz

```bash
# Launch RViz with Nav2 panel
rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz
```

Or manually add in RViz:
1. **Map** → Topic: `/map`
2. **LaserScan** → Topic: `/scan`
3. **Global Costmap** → Topic: `/global_costmap/costmap`
4. **Local Costmap** → Topic: `/local_costmap/costmap`
5. **Path** → Topic: `/plan`
6. **Nav2 Panel** → Add from Panels menu

### Step 3: Set Initial Pose

The robot needs to know where it is on the map:

1. In RViz, click **"2D Pose Estimate"** button
2. Click on the map where your robot actually is
3. Drag to set the orientation
4. Watch the laser scan align with the map

**If the alignment is poor:**
- Click "2D Pose Estimate" again
- Try different positions nearby
- Make sure you're in the right room!

### Step 4: Send Navigation Goals

Once localized:

1. Click **"Nav2 Goal"** button in RViz
2. Click on the map where you want the robot to go
3. Drag to set the desired orientation
4. Watch your robot autonomously navigate!

**The robot will:**
- Plan a collision-free path
- Follow the path using Regulated Pure Pursuit controller
- Avoid obstacles detected by lidar
- Execute recovery behaviors if stuck

### Step 5: Monitor Navigation

Watch these topics to debug issues:

```bash
# View the planned path
ros2 topic echo /plan

# Monitor velocity commands
ros2 topic echo /cmd_vel

# Check costmaps
ros2 topic echo /local_costmap/costmap

# View navigation status
ros2 topic echo /navigate_to_pose/_action/feedback
```

---

## Troubleshooting

### Issue: "No map received"

**Solutions:**
- Check that map file path is correct and absolute
- Verify `.yaml` and `.pgm` files exist
- Check map_server is running: `ros2 node list | grep map_server`

### Issue: Poor localization (laser scan doesn't match map)

**Solutions:**
- Set a better initial pose with "2D Pose Estimate"
- Drive the robot around slowly to help AMCL converge
- Check odometry: `ros2 topic echo /odom`
- Verify TF tree: `ros2 run tf2_tools view_frames`
- Tune AMCL parameters in `amcl_params.yaml`

### Issue: Robot won't move or plans weird paths

**Solutions:**
- Check velocity commands: `ros2 topic echo /cmd_vel`
- Verify costmaps in RViz (obstacles should be visible)
- Check robot footprint matches actual size
- Tune `robot_radius` in `nav2_params.yaml`
- Ensure `max_velocity` matches robot capabilities

### Issue: Robot gets stuck or oscillates

**Solutions:**
- Tune Pure Pursuit controller parameters:
  - Increase `lookahead_dist` for smoother paths
  - Adjust `desired_linear_vel` for speed
  - Tune `max_angular_accel` for turning
- Check inflation radius isn't too large
- Verify local costmap size is sufficient

### Issue: "Transform timeout" errors

**Solutions:**
- Check all TF transforms: `ros2 run tf2_tools view_frames`
- Verify robot_state_publisher is running
- Check `transform_tolerance` in config files
- Ensure clocks are synchronized (not using sim_time)

---

## Tuning Tips

### For Better Mapping (SLAM)

Edit `config/slam_toolbox_params.yaml`:

```yaml
# If map is too noisy:
minimum_travel_distance: 0.3  # Increase (process fewer scans)
minimum_travel_heading: 0.3

# If loop closures fail:
loop_search_maximum_distance: 5.0  # Increase search area
loop_match_minimum_response_coarse: 0.3  # Lower threshold

# If map drifts:
do_loop_closing: true  # Ensure this is true
```

### For Better Navigation (Nav2)

Edit `config/nav2_params.yaml`:

#### Adjust for Your Robot Size
```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      robot_radius: 0.20  # Increase if robot is bigger
```

#### Speed and Acceleration
```yaml
FollowPath:
  desired_linear_vel: 0.4  # Lower for safety, higher for speed
  max_angular_accel: 2.0   # Lower for smoother turns
```

#### Lookahead Distance (affects path following)
```yaml
FollowPath:
  lookahead_dist: 0.8      # Larger = less aggressive pursuit
  min_lookahead_dist: 0.4  # Minimum when going slow
```

#### Goal Tolerance
```yaml
general_goal_checker:
  xy_goal_tolerance: 0.2   # Position tolerance (meters)
  yaw_goal_tolerance: 0.3  # Orientation tolerance (radians)
```

#### Costmap Inflation (obstacle avoidance)
```yaml
inflation_layer:
  inflation_radius: 0.5    # How far to stay from obstacles
  cost_scaling_factor: 3.0 # How aggressive to avoid
```

### For Ackermann-Specific Tuning

Your robot uses **Regulated Pure Pursuit Controller**, optimized for Ackermann steering:

```yaml
FollowPath:
  use_rotate_to_heading: true       # Rotate before driving
  allow_reversing: false            # No backing up (Ackermann limitation)
  rotate_to_heading_min_angle: 0.785  # 45° - rotate if goal is behind
  max_angular_accel: 3.0            # Tuned for your robot
```

---

## Quick Reference Commands

### SLAM (Mapping)
```bash
# Launch SLAM to create map
ros2 launch gazebo_ackermann_steering_vehicle slam.launch.py

# Teleop while mapping
ros2 run ackermann_teleop teleop_node

# Save map
ros2 run nav2_map_server map_saver_cli -f my_map
```

### Nav2 (Navigation)
```bash
# Launch Nav2 with saved map
ros2 launch gazebo_ackermann_steering_vehicle navigation.launch.py \
    map:=/path/to/my_map.yaml

# Set 2D Pose Estimate in RViz
# Send Nav2 Goals in RViz
```

### Monitoring
```bash
# Check all topics
ros2 topic list

# Monitor specific topics
ros2 topic echo /odom
ros2 topic echo /scan
ros2 topic echo /cmd_vel

# View TF tree
ros2 run tf2_tools view_frames

# Check node status
ros2 node list
```

---

## Next Steps

1. ✅ **Test in a safe area first** - Start with low speeds
2. ✅ **Create multiple maps** - Different rooms/areas
3. ✅ **Tune parameters** - Optimize for your robot's behavior
4. ✅ **Set up waypoints** - Use waypoint_follower for patrol routes
5. ✅ **Add obstacle avoidance** - Test dynamic obstacle handling
6. ✅ **Integrate sensors** - Add IMU for better odometry
7. ✅ **Safety features** - Add emergency stop, battery monitoring

---

## Additional Resources

- [Nav2 Official Documentation](https://navigation.ros.org/)
- [SLAM Toolbox Documentation](https://github.com/SteveMacenski/slam_toolbox)
- [Regulated Pure Pursuit Controller](https://navigation.ros.org/configuration/packages/configuring-regulated-pp.html)
- [ROS2 TF2 Tutorial](https://docs.ros.org/en/rolling/Tutorials/Intermediate/Tf2/Tf2-Main.html)
- [Nav2 Tuning Guide](https://navigation.ros.org/tuning/index.html)

---

## Safety Reminders ⚠️

1. **Always test in a safe, open area first**
2. **Have an emergency stop method ready**
3. **Start with low velocities and increase gradually**
4. **Monitor battery levels during long runs**
5. **Check for loose cables that could interfere with wheels**
6. **Keep clear of the robot during autonomous operation**
7. **Test recovery behaviors before relying on them**

Happy navigating! 🤖🗺️
