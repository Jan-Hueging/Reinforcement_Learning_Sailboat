cmake_minimum_required(VERSION 3.8)
project(sailing_plugins)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# ------------------------------------------------------------
# Gazebo Harmonic 8 + Transport 13
# ------------------------------------------------------------
find_package(gz-sim8 REQUIRED)
find_package(gz-transport13 REQUIRED)

add_library(SailLimitPlugin SHARED
  src/SailLimitPlugin.cc
)

target_link_libraries(SailLimitPlugin
  gz-sim8::gz-sim8
  gz-transport13::gz-transport13
)

install(
  TARGETS SailLimitPlugin
  LIBRARY DESTINATION lib
)

add_library(SailingLiftDrag SHARED
  src/SailingLiftDrag.cc
  src/SailingLiftDrag.hh
)

target_link_libraries(SailingLiftDrag
  gz-sim8::gz-sim8
  gz-transport13::gz-transport13
)

install(
  TARGETS SailingLiftDrag
  LIBRARY DESTINATION lib
)

ament_package()
