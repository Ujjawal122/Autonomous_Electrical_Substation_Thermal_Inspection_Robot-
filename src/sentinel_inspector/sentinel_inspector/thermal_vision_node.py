import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool


class ThermalVisionNode(Node):
    """Detects thermal/hotspot anomalies from the inspection camera feed."""

    def __init__(self):
        super().__init__('thermal_vision_node')
        self.declare_parameter('red_threshold', 180)
        self.declare_parameter('min_hotspot_pixels', 150)

        self.bridge = CvBridge()
        self.anomaly_pub = self.create_publisher(Bool, '/thermal_anomaly', 10)
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10
        )
        self.get_logger().info('Thermal Vision Node active, listening on /camera/image_raw')

    def image_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().error(f'Failed to convert image: {exc}')
            return

        red_thresh = self.get_parameter('red_threshold').value
        min_pixels = self.get_parameter('min_hotspot_pixels').value

        # Detect strong red/orange regions (high R, lower G and B) as thermal hotspots
        b, g, r = cv2.split(cv_image)
        hotspot_mask = (r > red_thresh) & (r.astype(np.int16) - g.astype(np.int16) > 50)
        hotspot_count = int(np.count_nonzero(hotspot_mask))

        anomaly_msg = Bool()
        anomaly_msg.data = hotspot_count >= min_pixels
        self.anomaly_pub.publish(anomaly_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ThermalVisionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
