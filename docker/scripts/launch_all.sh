#!/bin/bash
# ============================================================
# launch_all.sh — Alle Simulation-Nodes in tmux starten
#
# Fenster:
#   0: physics    → Physik-Simulation
#   1: visualizer → Pygame-Visualisierung
#   2: training   → PPO-Training (Hauptfenster)
# ============================================================

SESSION="sailboat"

# Alte Session aufräumen
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo "⛵  Starte Sailboat-Simulation..."
sleep 1

# ── Fenster 0: Physik-Node ────────────────────────────────────
tmux new-session -d -s "$SESSION" -n "physics" \
    "source /opt/ros/jazzy/setup.bash && \
     source /ros2_ws/install/setup.bash && \
     echo '[Physics] Node startet...' && \
     ros2 run dummy_sailboat_sim dummy_node; \
     echo '[Physics] BEENDET – Enter drücken'; read"

# Kurz warten, bis ROS2 bereit ist
sleep 2

# ── Fenster 1: Visualizer-Node ────────────────────────────────
tmux new-window -t "$SESSION" -n "visualizer" \
    "source /opt/ros/jazzy/setup.bash && \
     source /ros2_ws/install/setup.bash && \
     echo '[Visualizer] Node startet...' && \
     ros2 run dummy_sailboat_sim visualizer \
         --ros-args --log-level WARN; \
     echo '[Visualizer] BEENDET – Enter drücken'; read"

sleep 1

# ── Fenster 2: Training ───────────────────────────────────────
tmux new-window -t "$SESSION" -n "training" \
    "source /opt/ros/jazzy/setup.bash && \
     source /ros2_ws/install/setup.bash && \
     echo '[Training] Starte PPO-Training...' && \
     python3 /ros2_ws/src/dummy_sailboat_sim/dummy_sailboat_sim/train.py; \
     echo '[Training] BEENDET – Enter drücken'; read"

# ── Statusanzeige ─────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║      ⛵  Sailboat Simulation gestartet!           ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  tmux-Steuerung:                                 ║"
echo "║    Ctrl+B → n    Nächstes Fenster                ║"
echo "║    Ctrl+B → p    Vorheriges Fenster              ║"
echo "║    Ctrl+B → w    Fensterübersicht                ║"
echo "║    Ctrl+B → d    Session verlassen (läuft weiter)║"
echo "║                                                  ║"
echo "║  Session beenden: tmux kill-session -t sailboat  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Training-Fenster aktiv schalten (relevanteste Ausgabe)
tmux select-window -t "$SESSION:training"
tmux attach-session -t "$SESSION"
