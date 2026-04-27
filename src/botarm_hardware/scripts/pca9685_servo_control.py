#!/usr/bin/env python3
import argparse
import time
from pathlib import Path

import yaml

import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def build_servos(cfg):
    pca_cfg = cfg["pca9685"]

    # On Ubuntu Pi this maps to /dev/i2c-1 for board.SCL/SDA.
    i2c = busio.I2C(board.SCL, board.SDA)

    pca = PCA9685(i2c, address=int(pca_cfg.get("address", 0x40)))
    pca.frequency = int(pca_cfg.get("frequency_hz", 50))

    servo_map = {}
    for joint, joint_cfg in cfg["joints"].items():
        ch = int(joint_cfg["channel"])
        servo_map[joint] = servo.Servo(
            pca.channels[ch],
            min_pulse=int(joint_cfg.get("min_pulse_us", 500)),
            max_pulse=int(joint_cfg.get("max_pulse_us", 2500)),
        )

    return pca, servo_map


def main():
    parser = argparse.ArgumentParser(description="Direct PCA9685 servo control for botarm joints")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "servo_map.yaml"))
    parser.add_argument("--joint", help="Joint name from servo_map.yaml")
    parser.add_argument("--deg", type=float, help="Target angle in degrees")
    parser.add_argument("--center-all", action="store_true", help="Center all configured servos")
    parser.add_argument("--sweep", action="store_true", help="Sweep one joint through min->max->center")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    pca, servo_map = build_servos(cfg)

    try:
        if args.center_all:
            for joint, s in servo_map.items():
                c = float(cfg["joints"][joint].get("center_deg", 90))
                s.angle = c
                print(f"{joint}: center -> {c} deg")
                time.sleep(0.08)
            return

        if not args.joint:
            raise SystemExit("--joint is required unless --center-all is used")
        if args.joint not in cfg["joints"]:
            raise SystemExit(f"Unknown joint '{args.joint}'")

        joint_cfg = cfg["joints"][args.joint]
        mn = float(joint_cfg.get("min_deg", 0))
        mx = float(joint_cfg.get("max_deg", 180))
        ctr = float(joint_cfg.get("center_deg", 90))

        s = servo_map[args.joint]

        if args.sweep:
            for target in [mn, mx, ctr]:
                s.angle = target
                print(f"{args.joint}: {target:.1f} deg")
                time.sleep(0.8)
            return

        if args.deg is None:
            raise SystemExit("--deg is required unless --sweep or --center-all is used")

        target = clamp(float(args.deg), mn, mx)
        s.angle = target
        print(f"{args.joint}: set to {target:.1f} deg (limits {mn:.1f}..{mx:.1f})")

    finally:
        pca.deinit()


if __name__ == "__main__":
    main()
