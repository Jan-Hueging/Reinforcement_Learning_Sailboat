# ============================================================
# Sailboat RL Simulation — Docker Image
# Basis: ROS2 Jazzy Desktop Full (Ubuntu 24.04)
# ============================================================
FROM osrf/ros:jazzy-desktop-full

# ── Build-Argumente & Umgebungsvariablen ─────────────────────
ARG DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── Systempakete ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git \
    tmux \
    # GUI-Backend für OpenCV (cv2.imshow im Visualizer-Node)
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgtk2.0-0 \
    # X11-Hilfsprogramme
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# ── ROS2-Workspace erstellen ──────────────────────────────────
RUN mkdir -p /ros2_ws/src

# ── Python-Abhängigkeiten installieren ────────────────────────
WORKDIR /ros2_ws/src/dummy_sailboat_sim
COPY requirements.txt /ros2_ws/src/dummy_sailboat_sim/
RUN pip install --no-cache-dir --break-system-packages \
    --ignore-installed numpy \
    -r requirements.txt

# ── Lokalen Code kopieren ─────────────────────────────────────
COPY . /ros2_ws/src/dummy_sailboat_sim/


#---test--------------------------------------------------------
RUN python3 -c "import setuptools; print(setuptools.__version__)"


# ── ROS2-Workspace kompilieren ────────────────────────────────
WORKDIR /ros2_ws
RUN bash -c "\
    source /opt/ros/jazzy/setup.bash && \
    colcon build \
        --symlink-install \
        --packages-select dummy_sailboat_sim \
        --cmake-args -DCMAKE_BUILD_TYPE=Release"
        
# ── Verzeichnis für trainierte Modelle ───────────────────────
RUN mkdir -p /ros2_ws/models

# ── Startup-Skripte kopieren ──────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/scripts/      /scripts/
RUN chmod +x /entrypoint.sh /scripts/*.sh

# ── Shell-Konfiguration ───────────────────────────────────────
RUN echo "source /opt/ros/jazzy/setup.bash"      >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash"    >> /root/.bashrc && \
    echo "export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-42}" >> /root/.bashrc

WORKDIR /ros2_ws

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
