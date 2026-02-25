import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import sys
import termios
import tty
import time
import select


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('keyboard_teleop')
        self.vel_pub = self.create_publisher(Float64, '/velocity', 10)
        self.steer_pub = self.create_publisher(Float64, '/steering_angle', 10)

        self.velocity = 0.0
        self.steering = 0.0

        # tuning
        self.vel_step = 0.1
        self.steer_step = 0.1
        self.max_vel = 2.0
        self.max_steer = 0.6  # radians

        self.get_logger().info(
            "Controls: W/S velocity  | A/D steering | SPACE stop | Ctrl+C quit"
        )

    def publish_once(self):
        self.vel_pub.publish(Float64(data=float(self.velocity)))
        self.steer_pub.publish(Float64(data=float(self.steering)))

    def clamp(self):
        self.velocity = max(-self.max_vel, min(self.max_vel, self.velocity))
        self.steering = max(-self.max_steer, min(self.max_steer, self.steering))

    def run(self):
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            last_pub = time.time()

            while rclpy.ok():
                # publish continuously at 10 Hz
                now = time.time()
                if now - last_pub >= 0.1:
                    self.publish_once()
                    last_pub = now

                # let ROS process internal events (important)
                rclpy.spin_once(self, timeout_sec=0.0)

                # non-blocking key read (works in many terminals)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)

                    if key == 'w':
                        self.velocity += self.vel_step
                    elif key == 's':
                        self.velocity -= self.vel_step
                    elif key == 'a':
                        self.steering += self.steer_step
                    elif key == 'd':
                        self.steering -= self.steer_step
                    elif key == ' ':
                        self.velocity = 0.0
                        self.steering = 0.0

                    self.clamp()
                    self.get_logger().info(
                        f"velocity={self.velocity:.2f}, steering={self.steering:.2f}"
                    )

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def main():
    rclpy.init()
    node = KeyboardTeleop()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    import select
    main()
