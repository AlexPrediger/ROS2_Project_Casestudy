#!/bin/bash
#
# Quick start script for real Ackermann robot with VESC and Lidar
# Usage: ./launch_real_robot.sh [vesc_port] [lidar_port]
#

set -e

# Default ports
VESC_PORT="${1:-/dev/ttyACM0}"
LIDAR_PORT="${2:-/dev/ttyUSB0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Real Robot Launch Script ===${NC}"
echo ""

# Check if ports exist
echo "Checking hardware connections..."
if [ ! -e "$VESC_PORT" ]; then
    echo -e "${RED}ERROR: VESC port $VESC_PORT not found!${NC}"
    echo "Available serial ports:"
    ls -l /dev/tty* | grep -E "ACM|USB"
    exit 1
fi

if [ ! -e "$LIDAR_PORT" ]; then
    echo -e "${YELLOW}WARNING: Lidar port $LIDAR_PORT not found!${NC}"
    echo "Available serial ports:"
    ls -l /dev/tty* | grep -E "ACM|USB"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ Hardware ports found${NC}"
echo ""

# Check permissions
echo "Checking port permissions..."
if [ ! -r "$VESC_PORT" ] || [ ! -w "$VESC_PORT" ]; then
    echo -e "${YELLOW}Setting VESC port permissions...${NC}"
    sudo chmod 666 "$VESC_PORT"
fi

if [ -e "$LIDAR_PORT" ]; then
    if [ ! -r "$LIDAR_PORT" ] || [ ! -w "$LIDAR_PORT" ]; then
        echo -e "${YELLOW}Setting Lidar port permissions...${NC}"
        sudo chmod 666 "$LIDAR_PORT"
    fi
fi

echo -e "${GREEN}✓ Port permissions OK${NC}"
echo ""

# Source ROS2 workspace
echo "Sourcing ROS2 workspace..."
cd "$(dirname "$0")/ros2_ws"

if [ ! -f "install/setup.bash" ]; then
    echo -e "${RED}ERROR: ROS2 workspace not built!${NC}"
    echo "Please run: cd ros2_ws && colcon build"
    exit 1
fi

source install/setup.bash
echo -e "${GREEN}✓ ROS2 workspace sourced${NC}"
echo ""

# Display configuration
echo -e "${GREEN}=== Configuration ===${NC}"
echo "VESC Port:  $VESC_PORT"
echo "Lidar Port: $LIDAR_PORT"
echo ""
echo "To stop the robot, press Ctrl+C"
echo ""

# Countdown
echo -e "${YELLOW}Starting in 3 seconds...${NC}"
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1

# Launch the robot
echo -e "${GREEN}Launching real robot...${NC}"
echo ""

ros2 launch gazebo_ackermann_steering_vehicle real_vehicle.launch.py \
    vesc_port:="$VESC_PORT" \
    lidar_port:="$LIDAR_PORT"
