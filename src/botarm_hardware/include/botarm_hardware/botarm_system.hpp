#ifndef BOTARM_HARDWARE__BOTARM_SYSTEM_HPP_
#define BOTARM_HARDWARE__BOTARM_SYSTEM_HPP_

#include <string>
#include <vector>

#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace botarm_hardware
{

class BotarmSystem : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(BotarmSystem)

  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

  hardware_interface::return_type write(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

private:
  std::vector<double> hw_states_;
  std::vector<double> hw_commands_;

  bool is_active_{false};
  bool loopback_mode_{true};

  std::string serial_port_{"/dev/ttyAMA0"};
  int baud_rate_{115200};
};

}  // namespace botarm_hardware

#endif  // BOTARM_HARDWARE__BOTARM_SYSTEM_HPP_
