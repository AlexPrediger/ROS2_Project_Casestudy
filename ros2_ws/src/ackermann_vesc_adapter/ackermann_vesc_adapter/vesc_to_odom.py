#!/usr/bin/env python3
"""
VESC to Odometry Converter
Subscribes to VESC state messages and publishes:
- Odometry (nav_msgs/Odometry)
- Joint states (sensor_msgs/JointState) for wheels
- TF transform (odom -> base_link)

Author: Auto-generated for real robot
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.time import Time

from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Quaternion, TransformStamped
from std_msgs.msg import Float64
from tf2_ros import TransformBroadcaster

# If vesc_msgs are available, use them. Otherwise, we'll use Float64 as fallback
try:
    from vesc_msgs.msg import VescStateStamped
    VESC_MSGS_AVAILABLE = True
except ImportError:
    VESC_MSGS_AVAILABLE = False


class VESCToOdom(Node):
    """
    Converts VESC motor feedback to odometry estimation.
    Publishes odometry, joint states, and TF transforms.
    """

    def __init__(self):
        super().__init__('vesc_to_odom')

        # Parameters
        self.declare_parameter('wheel_radius', 0.04)  # meters
        self.declare_parameter('wheelbase', 0.3)      # distance between front and rear axles
        self.declare_parameter('track_width', 0.2)    # distance between left and right wheels
        self.declare_parameter('erpm_to_speed_gain', 1.0 / 4614.0)  # ERPM to motor rad/s
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        # Get parameters
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheelbase = self.get_parameter('wheelbase').value
        self.track_width = self.get_parameter('track_width').value
        self.erpm_to_speed = self.get_parameter('erpm_to_speed_gain').value
        self.publish_tf = self.get_parameter('publish_tf').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        # State variables
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.vx = 0.0
        self.vtheta = 0.0
        self.last_time = self.get_clock().now()
        
        # Wheel positions (for joint states)
        self.rear_left_pos = 0.0
        self.rear_right_pos = 0.0
        self.front_left_pos = 0.0
        self.front_right_pos = 0.0
        self.steering_angle = 0.0

        # Publishers
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.joint_state_pub = self.create_publisher(JointState, 'joint_states', 10)
        
        if self.publish_tf:
            self.tf_broadcaster = TransformBroadcaster(self)

        # Subscribers
        if VESC_MSGS_AVAILABLE:
            self.vesc_state_sub = self.create_subscription(
                VescStateStamped,
                '/sensors/core',
                self.vesc_state_callback,
                10)
            self.get_logger().info('Using VescStateStamped messages')
        else:
            # Fallback: subscribe to motor speed directly
            self.motor_speed_sub = self.create_subscription(
                Float64,
                '/commands/motor/speed',
                self.motor_speed_callback,
                10)
            self.get_logger().info('VescStateStamped not available, using motor commands as fallback')

        # Subscribe to steering angle
        self.steering_sub = self.create_subscription(
            Float64,
            '/steering_angle',
            self.steering_callback,
            10)

        self.get_logger().info('VESC to Odometry node started')
        self.get_logger().info(f'Wheel radius: {self.wheel_radius}m, Wheelbase: {self.wheelbase}m')

    def steering_callback(self, msg):
        """Update current steering angle."""
        self.steering_angle = msg.data

    def vesc_state_callback(self, msg):
        """
        Process VESC state message and compute odometry.
        VescStateStamped contains speed_erpm, current, voltage, etc.
        """
        # Extract speed in ERPM (electrical RPM)
        erpm = msg.state.speed

        # Convert ERPM to wheel angular velocity
        # ERPM = motor_poles * motor_rpm
        # For wheel velocity: v = omega * r
        motor_angular_vel = erpm * self.erpm_to_speed  # rad/s
        wheel_linear_vel = motor_angular_vel * self.wheel_radius  # m/s

        self.compute_odometry(wheel_linear_vel)

    def motor_speed_callback(self, msg):
        """
        Fallback: use commanded motor speed if VESC state not available.
        Note: This is less accurate as it doesn't account for slippage.
        """
        erpm = msg.data
        motor_angular_vel = erpm * self.erpm_to_speed
        wheel_linear_vel = motor_angular_vel * self.wheel_radius
        
        self.compute_odometry(wheel_linear_vel)

    def compute_odometry(self, linear_velocity):
        """
        Compute odometry using Ackermann steering kinematics.
        
        For Ackermann steering:
        - Linear velocity from rear wheels (drive wheels)
        - Angular velocity computed from steering angle and wheelbase
        """
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        if dt <= 0.0:
            return
            
        # Ackermann steering: turning radius R = wheelbase / tan(steering_angle)
        # Angular velocity: omega = v / R = v * tan(steering_angle) / wheelbase
        if abs(self.steering_angle) > 0.001:  # Avoid division by zero
            turning_radius = self.wheelbase / math.tan(self.steering_angle)
            angular_velocity = linear_velocity / turning_radius
        else:
            angular_velocity = 0.0

        # Store velocities
        self.vx = linear_velocity
        self.vtheta = angular_velocity

        # Update pose using simple Euler integration
        delta_theta = angular_velocity * dt
        
        if abs(angular_velocity) > 0.001:
            # Circular arc motion
            delta_x = (linear_velocity / angular_velocity) * math.sin(delta_theta)
            delta_y = (linear_velocity / angular_velocity) * (1 - math.cos(delta_theta))
        else:
            # Straight line motion
            delta_x = linear_velocity * dt
            delta_y = 0.0

        # Transform to global frame
        self.x += delta_x * math.cos(self.theta) - delta_y * math.sin(self.theta)
        self.y += delta_x * math.sin(self.theta) + delta_y * math.cos(self.theta)
        self.theta += delta_theta
        
        # Normalize angle
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # Update wheel positions for joint states
        wheel_angular_vel = linear_velocity / self.wheel_radius
        self.rear_left_pos += wheel_angular_vel * dt
        self.rear_right_pos += wheel_angular_vel * dt
        # Front wheels depend on steering
        self.front_left_pos += wheel_angular_vel * dt
        self.front_right_pos += wheel_angular_vel * dt

        # Publish odometry and joint states
        self.publish_odometry(current_time)
        self.publish_joint_states(current_time)

        self.last_time = current_time

    def publish_odometry(self, timestamp):
        """Publish odometry message."""
        odom = Odometry()
        odom.header.stamp = timestamp.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame

        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0

        # Orientation (quaternion from yaw)
        odom.pose.pose.orientation = self.yaw_to_quaternion(self.theta)

        # Velocity
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.linear.y = 0.0
        odom.twist.twist.angular.z = self.vtheta

        # Covariance (rough estimates - tune based on your robot)
        odom.pose.covariance[0] = 0.01   # x
        odom.pose.covariance[7] = 0.01   # y
        odom.pose.covariance[14] = 0.01  # z
        odom.pose.covariance[21] = 0.05  # rot_x
        odom.pose.covariance[28] = 0.05  # rot_y
        odom.pose.covariance[35] = 0.1   # rot_z (yaw)

        odom.twist.covariance[0] = 0.01   # vx
        odom.twist.covariance[7] = 0.01   # vy
        odom.twist.covariance[14] = 0.01  # vz
        odom.twist.covariance[21] = 0.05  # vrot_x
        odom.twist.covariance[28] = 0.05  # vrot_y
        odom.twist.covariance[35] = 0.1   # vrot_z

        self.odom_pub.publish(odom)

        # Publish TF transform
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = timestamp.to_msg()
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_frame

            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation = self.yaw_to_quaternion(self.theta)

            self.tf_broadcaster.sendTransform(t)

    def publish_joint_states(self, timestamp):
        """Publish joint states for wheels and steering."""
        joint_state = JointState()
        joint_state.header.stamp = timestamp.to_msg()
        
        # Define joint names (must match URDF)
        joint_state.name = [
            'rear_left_wheel_joint',
            'rear_right_wheel_joint',
            'front_left_wheel_joint',
            'front_right_wheel_joint',
            'front_left_steer_joint',
            'front_right_steer_joint'
        ]
        
        # Positions (radians for revolute joints)
        joint_state.position = [
            self.rear_left_pos,
            self.rear_right_pos,
            self.front_left_pos,
            self.front_right_pos,
            self.steering_angle,  # Left front steering
            self.steering_angle   # Right front steering (same for parallel)
        ]
        
        # Velocities
        wheel_vel = self.vx / self.wheel_radius
        joint_state.velocity = [
            wheel_vel,  # rear_left
            wheel_vel,  # rear_right
            wheel_vel,  # front_left
            wheel_vel,  # front_right
            0.0,        # steering joints (assume quasi-static)
            0.0
        ]

        self.joint_state_pub.publish(joint_state)

    @staticmethod
    def yaw_to_quaternion(yaw):
        """Convert yaw angle to quaternion."""
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q


def main(args=None):
    rclpy.init(args=args)
    node = VESCToOdom()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
