import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class BatteryMonitorNode(Node):
    def __init__(self):
        super().__init__('battery_monitor_node')
        # Declare configurable ROS 2 parameters (great for live demo tuning!)
        self.declare_parameter('initial_soc', 100.0)
        self.declare_parameter('drain_rate_idle', 0.05)
        self.declare_parameter('drain_rate_moving', 0.25)

        self.soc = self.get_parameter('initial_soc').value
        self.is_moving = False
        self.at_dock = True

        self.soc_pub = self.create_publisher(Float32, '/battery_soc', 10)
        self.volt_pub = self.create_publisher(Float32, '/battery_voltage', 10)
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        self.timer = self.create_timer(1.0, self.update_battery)
        self.get_logger().info(f'Battery Monitor Active: Initial SoC = {self.soc:.1f}% (24.0V Nominal)')

    def cmd_callback(self, msg: Twist):
        speed = abs(msg.linear.x) + abs(msg.angular.z)
        self.is_moving = speed > 0.01

    def odom_callback(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.at_dock = math.hypot(x, y) < 0.45

    def update_battery(self):
        if self.at_dock and not self.is_moving:
            # Charging on green dock pad
            self.soc = min(100.0, self.soc + 1.5)
        else:
            drain = self.get_parameter('drain_rate_moving').value if self.is_moving else self.get_parameter('drain_rate_idle').value
            self.soc = max(0.0, self.soc - drain)

        # Map 0-100% SoC to 20.0V - 25.2V LiFePO4 pack curve
        voltage = 20.0 + (self.soc / 100.0) * 5.2

        soc_msg = Float32()
        soc_msg.data = float(self.soc)
        self.soc_pub.publish(soc_msg)

        volt_msg = Float32()
        volt_msg.data = round(float(voltage), 2)
        self.volt_pub.publish(volt_msg)

        if self.soc < 25.0 and not self.at_dock:
            self.get_logger().warn(f'LOW BATTERY WARNING: {self.soc:.1f}% ({voltage:.2f}V) - Return to Dock Recommended!')

def main(args=None):
    rclpy.init(args=args)
    node = BatteryMonitorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()