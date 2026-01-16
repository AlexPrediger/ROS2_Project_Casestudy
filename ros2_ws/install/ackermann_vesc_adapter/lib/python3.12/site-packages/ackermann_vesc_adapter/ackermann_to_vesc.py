import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import time

class AckermannToVESC(Node):

    def __init__(self):
        super().__init__('ackermann_to_vesc')

        # Subscribers (simulation side)
        self.sub_vel = self.create_subscription(
            Float64, '/velocity', self.vel_cb, 10)

        self.sub_steer = self.create_subscription(
            Float64, '/steering_angle', self.steer_cb, 10)

        # Publishers (VESC side)
        self.pub_motor = self.create_publisher(
            Float64, '/commands/motor/speed', 10)

        self.pub_servo = self.create_publisher(
            Float64, '/commands/servo/position', 10)

        # ---- TUNING PARAMETERS ----
        self.max_vehicle_speed = 4.0        # m/s (adjust if needed)
        self.max_erpm = 23250.0

        self.max_steer = 0.6                # radians
        self.servo_center = 0.50
        self.servo_range = 0.35             # 0.50 ± 0.35 → [0.15, 0.85]

        # Safety timeout
        self.last_cmd_time = time.time()
        self.timeout = 0.5                  # seconds

        self.velocity = 0.0
        self.steering = 0.0

        self.timer = self.create_timer(0.05, self.publish_cmd)  # 20 Hz

        self.get_logger().info("Ackermann → VESC adapter started")

    def vel_cb(self, msg):
        self.velocity = msg.data
        self.last_cmd_time = time.time()

    def steer_cb(self, msg):
        self.steering = msg.data
        self.last_cmd_time = time.time()

    def publish_cmd(self):
        # ---- SAFETY: stop if commands lost ----
        if time.time() - self.last_cmd_time > self.timeout:
            motor = 0.0
            servo = self.servo_center
        else:
            # Velocity → ERPM
            motor = (self.velocity / self.max_vehicle_speed) * self.max_erpm
            motor = max(-self.max_erpm, min(self.max_erpm, motor))

            # Steering → servo position
            servo = self.servo_center + (self.steering / self.max_steer) * self.servo_range
            servo = max(0.15, min(0.85, servo))

        self.pub_motor.publish(Float64(data=motor))
        self.pub_servo.publish(Float64(data=servo))


def main():
    rclpy.init()
    node = AckermannToVESC()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
