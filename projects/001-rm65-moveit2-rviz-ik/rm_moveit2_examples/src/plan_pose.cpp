#include <chrono>
#include <memory>
#include <thread>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <moveit/move_group_interface/move_group_interface.h>

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "rm65_plan_pose",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
  );

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() {
    executor.spin();
  });

  moveit::planning_interface::MoveGroupInterface move_group(node, "rm_group");

  RCLCPP_INFO(node->get_logger(), "MoveIt2 connected.");
  RCLCPP_INFO(node->get_logger(), "Planning frame: %s", move_group.getPlanningFrame().c_str());
  RCLCPP_INFO(node->get_logger(), "End effector link: %s", move_group.getEndEffectorLink().c_str());

  move_group.setPlanningTime(5.0);
  move_group.setMaxVelocityScalingFactor(0.1);
  move_group.setMaxAccelerationScalingFactor(0.1);

  double target_x = 0.25;
  double target_y = -0.25;
  double target_z = 0.45;

  if (!node->has_parameter("target_x")) {
    node->declare_parameter<double>("target_x", target_x);
  }
  if (!node->has_parameter("target_y")) {
    node->declare_parameter<double>("target_y", target_y);
  }
  if (!node->has_parameter("target_z")) {
    node->declare_parameter<double>("target_z", target_z);
  }

  target_x = node->get_parameter("target_x").as_double();
  target_y = node->get_parameter("target_y").as_double();
  target_z = node->get_parameter("target_z").as_double();

  geometry_msgs::msg::Pose target_pose;
  target_pose.orientation.w = 1.0;
  target_pose.position.x = target_x;
  target_pose.position.y = target_y;
  target_pose.position.z = target_z;
  auto marker_pub = node->create_publisher<visualization_msgs::msg::Marker>(
    "target_marker",
    rclcpp::QoS(1).transient_local()
  );

  visualization_msgs::msg::Marker marker;
  marker.header.frame_id = move_group.getPlanningFrame();
  marker.header.stamp = node->now();
  marker.ns = "rm65_target";
  marker.id = 0;
  marker.type = visualization_msgs::msg::Marker::SPHERE;
  marker.action = visualization_msgs::msg::Marker::ADD;
  marker.pose = target_pose;
  marker.scale.x = 0.05;
  marker.scale.y = 0.05;
  marker.scale.z = 0.05;
  marker.color.r = 1.0;
  marker.color.g = 0.1;
  marker.color.b = 0.1;
  marker.color.a = 1.0;
  marker.lifetime = rclcpp::Duration::from_seconds(30.0);

  marker_pub->publish(marker);
  rclcpp::sleep_for(std::chrono::milliseconds(500));
  marker_pub->publish(marker);
  RCLCPP_INFO(node->get_logger(), "Published target marker.");

  RCLCPP_INFO(node->get_logger(), "Keeping node alive for RViz marker subscription.");
  rclcpp::sleep_for(std::chrono::seconds(10));
  RCLCPP_INFO(
    node->get_logger(),
    "Target pose: x=%.3f, y=%.3f, z=%.3f, qw=%.3f",
    target_pose.position.x,
    target_pose.position.y,
    target_pose.position.z,
    target_pose.orientation.w
  );

  move_group.setPoseTarget(target_pose, "Link6");

  moveit::planning_interface::MoveGroupInterface::Plan plan;

  auto start_time = std::chrono::steady_clock::now();
  auto result = move_group.plan(plan);
  auto end_time = std::chrono::steady_clock::now();

  auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
    end_time - start_time
  ).count();

  if (result == moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_INFO(node->get_logger(), "Planning succeeded.");
    RCLCPP_INFO(node->get_logger(), "Measured planning time: %ld ms", elapsed_ms);

    const auto & trajectory = plan.trajectory_.joint_trajectory;
    RCLCPP_INFO(node->get_logger(), "Trajectory point count: %zu", trajectory.points.size());

    RCLCPP_INFO(node->get_logger(), "Joint names:");
    for (const auto & joint_name : trajectory.joint_names) {
      RCLCPP_INFO(node->get_logger(), "  %s", joint_name.c_str());
    }

    if (!trajectory.points.empty()) {
      const auto & first_point = trajectory.points.front();
      const auto & last_point = trajectory.points.back();

      RCLCPP_INFO(node->get_logger(), "First trajectory point:");
      for (size_t i = 0; i < trajectory.joint_names.size(); ++i) {
        RCLCPP_INFO(
          node->get_logger(),
          "  %s = %.4f rad",
          trajectory.joint_names[i].c_str(),
          first_point.positions[i]
        );
      }

      RCLCPP_INFO(node->get_logger(), "Last trajectory point:");
      for (size_t i = 0; i < trajectory.joint_names.size(); ++i) {
        RCLCPP_INFO(
          node->get_logger(),
          "  %s = %.4f rad",
          trajectory.joint_names[i].c_str(),
          last_point.positions[i]
        );
      }
    }
    RCLCPP_INFO(node->get_logger(), "Executing trajectory...");
    auto execute_result = move_group.execute(plan);

    if (execute_result == moveit::core::MoveItErrorCode::SUCCESS) {
      RCLCPP_INFO(node->get_logger(), "Execution succeeded.");
    } else {
      RCLCPP_ERROR(node->get_logger(), "Execution failed.");
    }
  } else {
    RCLCPP_ERROR(node->get_logger(), "Planning failed.");
  }

  executor.cancel();
  spinner.join();

  rclcpp::shutdown();
  return 0;
}
