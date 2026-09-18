#include "rm_isaac_ros2_control/rm_isaac_system.hpp"

#include <algorithm>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "rclcpp/rclcpp.hpp"

namespace rm_isaac_ros2_control
{
namespace
{

std::string to_isaac_joint_name(const std::string & ros_joint_name)
{
  if (ros_joint_name.rfind("joint", 0) == 0 && ros_joint_name.size() > 5) {
    return "joint_" + ros_joint_name.substr(5);
  }

  return ros_joint_name;
}

}  // namespace

hardware_interface::CallbackReturn RMIsaacSystem::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  hw_positions_.resize(info_.joints.size(), 0.0);
  hw_velocities_.resize(info_.joints.size(), 0.0);
  hw_commands_.resize(info_.joints.size(), 0.0);
  isaac_joint_names_.resize(info_.joints.size());

  for (size_t i = 0; i < info_.joints.size(); ++i) {
    isaac_joint_names_[i] = to_isaac_joint_name(info_.joints[i].name);
  }

  ros_node_ = rclcpp::Node::make_shared("rm_isaac_system_hardware");

  joint_command_pub_ = ros_node_->create_publisher<sensor_msgs::msg::JointState>(
    "/isaac_joint_commands",
    10
  );

  joint_state_sub_ = ros_node_->create_subscription<sensor_msgs::msg::JointState>(
    "/isaac_joint_states",
    10,
    std::bind(
      &RMIsaacSystem::isaac_joint_state_callback,
      this,
      std::placeholders::_1
    )
  );

  for (const auto & joint : info_.joints) {
    if (joint.command_interfaces.size() != 1) {
      RCLCPP_FATAL(
        rclcpp::get_logger("RMIsaacSystem"),
        "Joint '%s' has %zu command interfaces. Expected 1.",
        joint.name.c_str(),
        joint.command_interfaces.size()
      );
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.command_interfaces[0].name != hardware_interface::HW_IF_POSITION) {
      RCLCPP_FATAL(
        rclcpp::get_logger("RMIsaacSystem"),
        "Joint '%s' command interface is '%s'. Expected '%s'.",
        joint.name.c_str(),
        joint.command_interfaces[0].name.c_str(),
        hardware_interface::HW_IF_POSITION
      );
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces.size() < 1) {
      RCLCPP_FATAL(
        rclcpp::get_logger("RMIsaacSystem"),
        "Joint '%s' has no state interfaces.",
        joint.name.c_str()
      );
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  RCLCPP_INFO(
    rclcpp::get_logger("RMIsaacSystem"),
    "Initialized RMIsaacSystem with %zu joints.",
    info_.joints.size()
  );

  RCLCPP_INFO(
    rclcpp::get_logger("RMIsaacSystem"),
    "Publishing commands to /isaac_joint_commands and subscribing to /isaac_joint_states."
  );

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface>
RMIsaacSystem::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (size_t i = 0; i < info_.joints.size(); ++i) {
    state_interfaces.emplace_back(
      hardware_interface::StateInterface(
        info_.joints[i].name,
        hardware_interface::HW_IF_POSITION,
        &hw_positions_[i]
      )
    );

    state_interfaces.emplace_back(
      hardware_interface::StateInterface(
        info_.joints[i].name,
        hardware_interface::HW_IF_VELOCITY,
        &hw_velocities_[i]
      )
    );
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface>
RMIsaacSystem::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  for (size_t i = 0; i < info_.joints.size(); ++i) {
    command_interfaces.emplace_back(
      hardware_interface::CommandInterface(
        info_.joints[i].name,
        hardware_interface::HW_IF_POSITION,
        &hw_commands_[i]
      )
    );
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn RMIsaacSystem::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  for (size_t i = 0; i < hw_positions_.size(); ++i) {
    hw_commands_[i] = hw_positions_[i];
  }

  RCLCPP_INFO(rclcpp::get_logger("RMIsaacSystem"), "Activated RMIsaacSystem.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RMIsaacSystem::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("RMIsaacSystem"), "Deactivated RMIsaacSystem.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RMIsaacSystem::read(
  const rclcpp::Time & /*time*/,
  const rclcpp::Duration & /*period*/)
{
  if (ros_node_) {
    rclcpp::spin_some(ros_node_);
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type RMIsaacSystem::write(
  const rclcpp::Time & /*time*/,
  const rclcpp::Duration & /*period*/)
{
  if (!joint_command_pub_) {
    return hardware_interface::return_type::ERROR;
  }

  sensor_msgs::msg::JointState command_msg;
  command_msg.header.stamp = ros_node_->now();
  command_msg.name = isaac_joint_names_;
  command_msg.position = hw_commands_;

  joint_command_pub_->publish(command_msg);

  return hardware_interface::return_type::OK;
}

void RMIsaacSystem::isaac_joint_state_callback(
  const sensor_msgs::msg::JointState::SharedPtr msg)
{
  for (size_t i = 0; i < info_.joints.size(); ++i) {
    const auto & isaac_joint_name = isaac_joint_names_[i];

    auto it = std::find(msg->name.begin(), msg->name.end(), isaac_joint_name);
    if (it == msg->name.end()) {
      continue;
    }

    const auto index = static_cast<size_t>(std::distance(msg->name.begin(), it));

    if (index < msg->position.size()) {
      hw_positions_[i] = msg->position[index];
    }

    if (index < msg->velocity.size()) {
      hw_velocities_[i] = msg->velocity[index];
    }
  }
}

}  // namespace rm_isaac_ros2_control

PLUGINLIB_EXPORT_CLASS(
  rm_isaac_ros2_control::RMIsaacSystem,
  hardware_interface::SystemInterface
)
