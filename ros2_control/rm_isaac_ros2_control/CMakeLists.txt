cmake_minimum_required(VERSION 3.8)
project(rm_isaac_ros2_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(sensor_msgs REQUIRED)
add_library(
  rm_isaac_ros2_control
  SHARED
  src/rm_isaac_system.cpp
)

target_include_directories(
  rm_isaac_ros2_control
  PUBLIC
  include
)

ament_target_dependencies(
  rm_isaac_ros2_control
  rclcpp
  hardware_interface
  pluginlib
  rclcpp_lifecycle
  sensor_msgs
)

pluginlib_export_plugin_description_file(
  hardware_interface
  rm_isaac_ros2_control.xml
)

install(
  TARGETS rm_isaac_ros2_control
  DESTINATION lib
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  FILES rm_isaac_ros2_control.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_export_include_directories(include)
ament_export_libraries(rm_isaac_ros2_control)
ament_export_dependencies(
  rclcpp
  hardware_interface
  pluginlib
  rclcpp_lifecycle
  sensor_msgs
)

ament_package()
