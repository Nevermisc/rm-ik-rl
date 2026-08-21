#include <chrono>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/point.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <moveit/move_group_interface/move_group_interface.h>

namespace
{
visualization_msgs::msg::Marker makeTargetMarker(
  const rclcpp::Node::SharedPtr & node,
  const std::string & frame_id,
  const geometry_msgs::msg::Pose & target_pose)
{
  visualization_msgs::msg::Marker marker;
  marker.header.frame_id = frame_id;
  marker.header.stamp = node->now();
  marker.ns = "rm65_interactive_target";
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
  marker.lifetime = rclcpp::Duration::from_seconds(0.0);
  return marker;
}
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "rm65_interactive_pose_commander",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
  );

  std::mutex target_mutex;
  std::condition_variable target_cv;
  std::queue<geometry_msgs::msg::Point> target_queue;

  auto target_sub = node->create_subscription<geometry_msgs::msg::Point>(
    "rm65_target_point",
    rclcpp::QoS(10),
    [&](const geometry_msgs::msg::Point::SharedPtr msg) {
      {
        std::lock_guard<std::mutex> lock(target_mutex);
        target_queue.push(*msg);
      }
      target_cv.notify_one();
    }
  );

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() {
    executor.spin();
  });

  moveit::planning_interface::MoveGroupInterface move_group(node, "rm_group");

  move_group.setPlanningTime(5.0);
  move_group.setNumPlanningAttempts(10);
  move_group.setMaxVelocityScalingFactor(0.1);
  move_group.setMaxAccelerationScalingFactor(0.1);

  const std::string end_effector_link = move_group.getEndEffectorLink().empty()
    ? "Link6"
    : move_group.getEndEffectorLink();

  auto marker_pub = node->create_publisher<visualization_msgs::msg::Marker>(
    "interactive_target_marker",
    rclcpp::QoS(1).transient_local()
  );

  RCLCPP_INFO(node->get_logger(), "MoveIt2 connected.");
  RCLCPP_INFO(node->get_logger(), "Planning frame: %s", move_group.getPlanningFrame().c_str());
  RCLCPP_INFO(node->get_logger(), "End effector link: %s", end_effector_link.c_str());
  RCLCPP_INFO(node->get_logger(), "Waiting for target points on topic: /rm65_target_point");
  RCLCPP_INFO(node->get_logger(), "Example command:");
  RCLCPP_INFO(
    node->get_logger(),
    "ros2 topic pub --once /rm65_target_point geometry_msgs/msg/Point '{x: 0.30, y: 0.20, z: 0.40}'"
  );

  while (rclcpp::ok()) {
    geometry_msgs::msg::Point target_point;
    {
      std::unique_lock<std::mutex> lock(target_mutex);
      target_cv.wait(lock, [&]() {
        return !target_queue.empty() || !rclcpp::ok();
      });

      if (!rclcpp::ok()) {
        break;
      }

      target_point = target_queue.front();
      target_queue.pop();
    }

    geometry_msgs::msg::Pose target_pose;
    target_pose.orientation.w = 1.0;
    target_pose.position.x = target_point.x;
    target_pose.position.y = target_point.y;
    target_pose.position.z = target_point.z;

    auto marker = makeTargetMarker(node, move_group.getPlanningFrame(), target_pose);
    marker_pub->publish(marker);

    RCLCPP_INFO(
      node->get_logger(),
      "New target: x=%.3f, y=%.3f, z=%.3f, qw=%.3f",
      target_pose.position.x,
      target_pose.position.y,
      target_pose.position.z,
      target_pose.orientation.w
    );

    move_group.setStartStateToCurrentState();
    move_group.setPoseTarget(target_pose, end_effector_link);

    moveit::planning_interface::MoveGroupInterface::Plan plan;

    const auto start_time = std::chrono::steady_clock::now();
    const auto plan_result = move_group.plan(plan);
    const auto end_time = std::chrono::steady_clock::now();

    const auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
      end_time - start_time
    ).count();

    if (plan_result != moveit::core::MoveItErrorCode::SUCCESS) {
      RCLCPP_ERROR(node->get_logger(), "Planning failed. The target may be unreachable with the current orientation.");
      move_group.clearPoseTargets();
      continue;
    }

    const auto & trajectory = plan.trajectory_.joint_trajectory;
    RCLCPP_INFO(node->get_logger(), "Planning succeeded in %ld ms.", elapsed_ms);
    RCLCPP_INFO(node->get_logger(), "Trajectory point count: %zu", trajectory.points.size());

    if (!trajectory.points.empty()) {
      const auto & last_point = trajectory.points.back();
      RCLCPP_INFO(node->get_logger(), "Final joint target:");
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
    const auto execute_result = move_group.execute(plan);

    if (execute_result == moveit::core::MoveItErrorCode::SUCCESS) {
      RCLCPP_INFO(node->get_logger(), "Execution succeeded. Waiting for the next target.");
    } else {
      RCLCPP_ERROR(node->get_logger(), "Execution failed.");
    }

    move_group.clearPoseTargets();
  }

  executor.cancel();
  spinner.join();

  rclcpp::shutdown();
  return 0;
}
