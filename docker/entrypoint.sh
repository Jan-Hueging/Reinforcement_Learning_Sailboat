#!/bin/bash
# ============================================================
# Entrypoint: ROS2 & Workspace-Umgebung aktivieren
# ============================================================
set -e

# ROS2 Jazzy sourcen
source /opt/ros/jazzy/setup.bash

# Kompilierten Workspace sourcen (falls vorhanden)
if [ -f /ros2_ws/install/setup.bash ]; then
    source /ros2_ws/install/setup.bash
fi

# ROS_DOMAIN_ID setzen (Isolation mehrerer Simulationen)
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

exec "$@"
