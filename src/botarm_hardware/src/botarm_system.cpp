#include "botarm_hardware/botarm_system.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cctype>
#include <string>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "rclcpp/rclcpp.hpp"

namespace botarm_hardware
{

hardware_interface::CallbackReturn BotarmSystem::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
    hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  const auto it_loopback = info_.hardware_parameters.find("loopback_mode");
  if (it_loopback != info_.hardware_parameters.end()) {
    std::string v = it_loopback->second;
    std::transform(v.begin(), v.end(), v.begin(), [](unsigned char c) {return static_cast<char>(std::tolower(c));});
    loopback_mode_ = !(v == "false" || v == "0" || v == "off" || v == "no");
  }

  const auto it_serial_port = info_.hardware_parameters.find("serial_port");
  if (it_serial_port != info_.hardware_parameters.end()) {
    serial_port_ = it_serial_port->second;
  }

  const auto it_baud = info_.hardware_parameters.find("baud_rate");
  if (it_baud != info_.hardware_parameters.end()) {
    baud_rate_ = std::atoi(it_baud->second.c_str());
    if (baud_rate_ <= 0) {
      RCLCPP_ERROR(rclcpp::get_logger("BotarmSystem"), "Invalid baud_rate: %s", it_baud->second.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  for (const auto & joint : info_.joints) {
    if (joint.command_interfaces.size() != 1 ||
      joint.command_interfaces[0].name != hardware_interface::HW_IF_POSITION)
    {
      RCLCPP_ERROR(
        rclcpp::get_logger("BotarmSystem"),
        "Joint '%s' must have exactly one command interface: position",
        joint.name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces.size() != 1 ||
      joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION)
    {
      RCLCPP_ERROR(
        rclcpp::get_logger("BotarmSystem"),
        "Joint '%s' must have exactly one state interface: position",
        joint.name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  hw_states_.assign(info_.joints.size(), 0.0);
  hw_commands_.assign(info_.joints.size(), 0.0);

  RCLCPP_INFO(
    rclcpp::get_logger("BotarmSystem"),
    "Initialized with %zu joints. loopback_mode=%s serial_port=%s baud_rate=%d",
    info_.joints.size(),
    loopback_mode_ ? "true" : "false",
    serial_port_.c_str(),
    baud_rate_);

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> BotarmSystem::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  state_interfaces.reserve(info_.joints.size());

  for (size_t i = 0; i < info_.joints.size(); ++i) {
    state_interfaces.emplace_back(
      info_.joints[i].name,
      hardware_interface::HW_IF_POSITION,
      &hw_states_[i]);
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> BotarmSystem::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  command_interfaces.reserve(info_.joints.size());

  for (size_t i = 0; i < info_.joints.size(); ++i) {
    command_interfaces.emplace_back(
      info_.joints[i].name,
      hardware_interface::HW_IF_POSITION,
      &hw_commands_[i]);
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn BotarmSystem::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  is_active_ = true;

  // Start from the current measured state to avoid sudden jumps.
  hw_commands_ = hw_states_;

  RCLCPP_INFO(rclcpp::get_logger("BotarmSystem"), "Activated botarm hardware interface");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn BotarmSystem::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  is_active_ = false;
  RCLCPP_INFO(rclcpp::get_logger("BotarmSystem"), "Deactivated botarm hardware interface");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type BotarmSystem::read(
  const rclcpp::Time & /*time*/,
  const rclcpp::Duration & /*period*/)
{
  if (!is_active_) {
    return hardware_interface::return_type::OK;
  }

  if (loopback_mode_) {
    // In loopback mode, state follows commands deterministically.
    hw_states_ = hw_commands_;
    return hardware_interface::return_type::OK;
  }

  // TODO(emmanuel): Replace this block with encoder read from your motor bus.
  // Keep states bounded/safe in case bus integration is incomplete.
  for (auto & s : hw_states_) {
    if (!std::isfinite(s)) {
      s = 0.0;
    }
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type BotarmSystem::write(
  const rclcpp::Time & /*time*/,
  const rclcpp::Duration & /*period*/)
{
  if (!is_active_) {
    return hardware_interface::return_type::OK;
  }

  // Assume all actuators are 180-degree servos centered at 0 rad:
  // -90 deg .. +90 deg  <=>  -pi/2 .. +pi/2
  constexpr double kServoMinRad = -1.57079632679;
  constexpr double kServoMaxRad = 1.57079632679;
  constexpr double kRadToDeg = 57.2957795131;

  std::vector<double> servo_degrees;
  servo_degrees.reserve(hw_commands_.size());

  // Clamp non-finite commands before touching hardware.
  for (auto & c : hw_commands_) {
    if (!std::isfinite(c)) {
      c = 0.0;
    }
    c = std::clamp(c, kServoMinRad, kServoMaxRad);
    servo_degrees.push_back((c - kServoMinRad) * kRadToDeg);  // map [-90, +90] -> [0, 180]
  }

  if (loopback_mode_) {
    return hardware_interface::return_type::OK;
  }

  // TODO(emmanuel): Send hw_commands_ to your Pi motor driver transport
  // (UART/CAN/SPI/I2C) and handle ACK/timeout/error paths here.
  // `servo_degrees[i]` already contains per-joint command in [0, 180].

  return hardware_interface::return_type::OK;
}

}  // namespace botarm_hardware

PLUGINLIB_EXPORT_CLASS(botarm_hardware::BotarmSystem, hardware_interface::SystemInterface)
