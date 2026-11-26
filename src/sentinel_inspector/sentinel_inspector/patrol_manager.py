import time
import csv
import os
from datetime import datetime
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class TelemetryListener(Node):
    def __init__(self):
        super().__init__('telemetry_listener')
        self.fault_detected = False
        self.battery_soc = 100.0
        self.fault_sub = self.create_subscription(Bool, '/thermal_anomaly', self.fault_cb, 10)
        self.batt_sub = self.create_subscription(Float32, '/battery_soc', self.batt_cb, 10)

    def fault_cb(self, msg: Bool):
        self.fault_detected = msg.data

    def batt_cb(self, msg: Float32):
        self.battery_soc = msg.data

def create_pose(navigator: BasicNavigator, x: float, y: float, yaw_w: float = 1.0, yaw_z: float = 0.0) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = yaw_w
    pose.pose.orientation.z = yaw_z
    return pose

def main():
    rclpy.init()
    navigator = BasicNavigator()
    telemetry = TelemetryListener()

    initial_pose = create_pose(navigator, 0.0, 0.0, 1.0, 0.0)
    navigator.setInitialPose(initial_pose)
    print("Waiting for Nav2 to become active...")
    navigator.waitUntilNav2Active()

    checkpoints = [
        {"name": "Transformer_Bay_A", "x": 1.8, "y": 2.5, "w": 1.0, "z": 0.0},
        {"name": "HV_Switchgear_Panel_B", "x": 1.8, "y": -2.5, "w": 1.0, "z": 0.0},
        {"name": "Battery_Bank_C", "x": -1.8, "y": 2.5, "w": 0.0, "z": 1.0},
    ]

    report_path = os.path.expanduser('~/substation_inspection_report.csv')
    low_battery_abort = False

    with open(report_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Equipment_Bay', 'X_Coord', 'Y_Coord', 'Battery_SoC', 'Thermal_Status'])

        for cp in checkpoints:
            rclpy.spin_once(telemetry, timeout_sec=0.1)
            if telemetry.battery_soc < 25.0:
                print(f"\n[CRITICAL FAIL-SAFE] Battery SoC at {telemetry.battery_soc:.1f}% (<25%). Aborting remaining patrol!")
                low_battery_abort = True
                break

            print(f"\n---> Navigating to {cp['name']} ({cp['x']}, {cp['y']}) | Battery: {telemetry.battery_soc:.1f}%...")
            goal = create_pose(navigator, cp['x'], cp['y'], cp['w'], cp['z'])
            navigator.goToPose(goal)

            while not navigator.isTaskComplete():
                rclpy.spin_once(telemetry, timeout_sec=0.2)
                if telemetry.battery_soc < 25.0:
                    print(f"\n[EMERGENCY RTD] Battery dropped to {telemetry.battery_soc:.1f}% mid-route! Canceling goal...")
                    navigator.cancelTask()
                    low_battery_abort = True
                    break

            if low_battery_abort:
                break

            if navigator.getResult() == TaskResult.SUCCEEDED:
                print(f"Arrived at {cp['name']}. Scanning thermal signature for 3 seconds...")
                fault_found = False
                for _ in range(15):
                    rclpy.spin_once(telemetry, timeout_sec=0.2)
                    if telemetry.fault_detected:
                        fault_found = True

                status = "CRITICAL: OVERHEATING HOTSPOT DETECTED" if fault_found else "NORMAL: HEALTHY"
                print(f"[{cp['name']}] Result: {status}")
                writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cp['name'], cp['x'], cp['y'], f"{telemetry.battery_soc:.1f}%", status])

    print("\n---> Returning to Green Charging Dock Pad (0.0, 0.0)...")
    dock_pose = create_pose(navigator, 0.0, 0.0, 1.0, 0.0)
    navigator.goToPose(dock_pose)
    while not navigator.isTaskComplete():
        time.sleep(0.2)

    print(f"Sentinel Docked & Recharging! Inspection report saved to: {report_path}")
    telemetry.destroy_node()
    navigator.lifecycleShutdown()
    rclpy.shutdown()

if __name__ == '__main__':
    main()