#!/usr/bin/env python3
import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import yaml

import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo


class Pca9685HardwareBridge(Node):
    def __init__(self):
        super().__init__('pca9685_bridge')

        # Prefer a portable workspace-relative default and allow override via ROS param.
        default_cfg = os.path.expanduser('~/agropilot2working_ws/src/botarm_hardware/config/servo_map.yaml')
        self.declare_parameter('config_path', default_cfg)
        config_path = self.get_parameter('config_path').get_parameter_value().string_value

        if not os.path.exists(config_path):
            self.get_logger().error(f"CRITICAL: Config file not found at {config_path}!")
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            full_config = yaml.safe_load(f)
            self.joint_config = full_config.get('joints', {})
            pca_settings = full_config.get('pca9685', {})

        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(self.i2c, address=pca_settings.get('address', 0x40))
            self.pca.frequency = pca_settings.get('frequency_hz', 50)

            self.servos = {}
            for name, info in self.joint_config.items():
                chan = info['channel']
                self.servos[name] = servo.Servo(self.pca.channels[chan])

            self.get_logger().info(f"Successfully initialized {len(self.servos)} joints!")
        except Exception as e:
            self.get_logger().error(f"HARDWARE FAILURE: {e}")
            return

        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.listener_callback,
            10
        )

    def listener_callback(self, msg):
        for i, name in enumerate(msg.name):
            if name in self.joint_config:
                conf = self.joint_config[name]
                center = conf.get('center_deg', 90)
                min_limit = conf.get('min_deg', 0)
                max_limit = conf.get('max_deg', 180)

                rad = msg.position[i]
                target_deg = (rad * 180.0 / 3.14159) + center
                target_deg = max(min_limit, min(max_limit, target_deg))

                try:
                    self.servos[name].angle = target_deg
                except Exception:
                    # Avoid flooding logs during high-rate updates.
                    pass


def main(args=None):
    rclpy.init(args=args)
    node = Pca9685HardwareBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if hasattr(node, 'pca'):
            node.pca.deinit()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
