#include <chrono>
#include <cmath>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/point.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <moveit_msgs/msg/robot_trajectory.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <moveit/move_group_interface/move_group_interface.h>

namespace
{
constexpr double kPi = 3.14159265358979323846;

visualization_msgs::msg::Marker makeCircleMarker(
  const rclcpp::Node::SharedPtr & node,
  const std::string & frame_id,
  const std::vector<geometry_msgs::msg::Pose> & waypoints)
{
  visualization_msgs::msg::Marker marker;
  marker.header.frame_id = frame_id;
  marker.header.stamp = node->now();
  marker.ns = "rm65_circle_path";
  marker.id = 0;
  marker.type = visualization_msgs::msg::Marker::LINE_STRIP;
  marker.action = visualization_msgs::msg::Marker::ADD;
  marker.scale.x = 0.01;
  marker.color.r = 0.1;
  marker.color.g = 1.0;
  marker.color.b = 0.1;
  marker.color.a = 1.0;
  marker.lifetime = rclcpp::Duration::from_seconds(0.0);

  for (const auto & pose : waypoints) {
    geometry_msgs::msg::Point point;
    point.x = pose.position.x;
    point.y = pose.position.y;
    point.z = pose.position.z;
    marker.points.push_back(point);
  }

  return marker;
}

std::vector<geometry_msgs::msg::Pose> makeVerticalCircleWaypoints(
  double center_x,
  double center_y,
  double center_z,
  double radius,
  int samples)
{
  std::vector<geometry_msgs::msg::Pose> waypoints;
  waypoints.reserve(static_cast<size_t>(samples + 1));

  for (int i = 0; i <= samples; ++i) {
    const double theta = 2.0 * kPi * static_cast<double>(i) / static_cast<double>(samples);

    geometry_msgs::msg::Pose pose;
    pose.orientation.w = 1.0;
    pose.position.x = center_x;
    pose.position.y = center_y + radius * std::cos(theta);
    pose.position.z = center_z + radius * std::sin(theta);
    waypoints.push_back(pose);
  }

  return waypoints;
}
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "rm65_draw_circle",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
  );

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() {
    executor.spin();
  });

  moveit::planning_interface::MoveGroupInterface move_group(node, "rm_group");

  move_group.setPlanningTime(8.0);
  move_group.setNumPlanningAttempts(10);
  move_group.setMaxVelocityScalingFactor(0.08);
  move_group.setMaxAccelerationScalingFactor(0.08);

  double center_x = node->get_parameter("center_x").as_double();
  double center_y = node->get_parameter("center_y").as_double();
  double center_z = node->get_parameter("center_z").as_double();
  double radius = node->get_parameter("radius").as_double();
  int samples = static_cast<int>(node->get_parameter("samples").as_int());
  double eef_step = node->get_parameter("eef_step").as_double();

  if (samples < 12) {
    RCLCPP_WARN(node->get_logger(), "samples is too small. Using 12 instead.");
    samples = 12;
  }
  if (radius <= 0.0) {
    RCLCPP_WARN(node->get_logger(), "radius must be positive. Using 0.03 m instead.");
    radius = 0.03;
  }
  if (eef_step <= 0.0) {
    RCLCPP_WARN(node->get_logger(), "eef_step must be positive. Using 0.01 m instead.");
    eef_step = 0.01;
  }

  const std::string end_effector_link = move_group.getEndEffectorLink().empty()
    ? "Link6"
    : move_group.getEndEffectorLink();

  auto marker_pub = node->create_publisher<visualization_msgs::msg::Marker>(
    "circle_path_marker",
    rclcpp::QoS(1).transient_local()
  );

  RCLCPP_INFO(node->get_logger(), "MoveIt2 connected.");
  RCLCPP_INFO(node->get_logger(), "Planning frame: %s", move_group.getPlanningFrame().c_str());
  RCLCPP_INFO(node->get_logger(), "End effector link: %s", end_effector_link.c_str());
  RCLCPP_INFO(
    node->get_logger(),
    "Circle: center=(%.3f, %.3f, %.3f), radius=%.3f, samples=%d, eef_step=%.3f",
    center_x,
    center_y,
    center_z,
    radius,
    samples,
    eef_step
  );

  auto waypoints = makeVerticalCircleWaypoints(center_x, center_y, center_z, radius, samples);
  marker_pub->publish(makeCircleMarker(node, move_group.getPlanningFrame(), waypoints));
  rclcpp::sleep_for(std::chrono::milliseconds(500));
  marker_pub->publish(makeCircleMarker(node, move_group.getPlanningFrame(), waypoints));

  const auto & first_pose = waypoints.front();
  RCLCPP_INFO(
    node->get_logger(),
    "Moving to circle start point: x=%.3f, y=%.3f, z=%.3f",
    first_pose.position.x,
    first_pose.position.y,
    first_pose.position.z
  );

  move_group.setStartStateToCurrentState();
  move_group.setPoseTarget(first_pose, end_effector_link);

  moveit::planning_interface::MoveGroupInterface::Plan approach_plan;
  const auto approach_result = move_group.plan(approach_plan);

  if (approach_result != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(node->get_logger(), "Failed to plan to the circle start point.");
    executor.cancel();
    spinner.join();
    rclcpp::shutdown();
    return 1;
  }

  RCLCPP_INFO(node->get_logger(), "Executing approach trajectory...");
  const auto approach_execute_result = move_group.execute(approach_plan);
  if (approach_execute_result != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(node->get_logger(), "Failed to execute approach trajectory.");
    executor.cancel();
    spinner.join();
    rclcpp::shutdown();
    return 1;
  }

  move_group.clearPoseTargets();
  rclcpp::sleep_for(std::chrono::milliseconds(500));

  RCLCPP_INFO(node->get_logger(), "Computing Cartesian circle path...");

  moveit_msgs::msg::RobotTrajectory circle_trajectory;
  const double jump_threshold = 0.0;
  const double fraction = move_group.computeCartesianPath(
    waypoints,
    eef_step,
    jump_threshold,
    circle_trajectory
  );

  RCLCPP_INFO(node->get_logger(), "Cartesian path fraction: %.3f", fraction);

  if (fraction < 0.80) {
    RCLCPP_ERROR(
      node->get_logger(),
      "Cartesian path coverage is too low. Try a smaller radius or a different center."
    );
    executor.cancel();
    spinner.join();
    rclcpp::shutdown();
    return 1;
  }

  moveit::planning_interface::MoveGroupInterface::Plan circle_plan;
  circle_plan.trajectory_ = circle_trajectory;

  RCLCPP_INFO(node->get_logger(), "Executing circle trajectory...");
  const auto circle_execute_result = move_group.execute(circle_plan);

  if (circle_execute_result == moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_INFO(node->get_logger(), "Circle execution succeeded.");
  } else {
    RCLCPP_ERROR(node->get_logger(), "Circle execution failed.");
  }

  executor.cancel();
  spinner.join();
  rclcpp::shutdown();
  return 0;
}
