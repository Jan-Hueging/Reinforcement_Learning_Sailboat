# ============================================================
# Makefile — Sailboat RL Simulation
# Verwendung: make <ziel>
# ============================================================

IMAGE  := sailboat_sim:latest
COMPOSE := docker compose

.PHONY: help build pull setup run-all run-physics run-visualizer \
        run-training shell logs clean rebuild

# ── Standard: Hilfe anzeigen ─────────────────────────────────
help:
	@echo ""
	@echo "⛵  Sailboat RL Simulation — Verfügbare Befehle"
	@echo "════════════════════════════════════════════════"
	@echo "  make build          Image bauen"
	@echo "  make pull           Basis-Image herunterladen"
	@echo "  make setup          X11 einrichten + Image bauen"
	@echo ""
	@echo "  make run-all        Alle Nodes (tmux, All-in-One)"
	@echo "  make run-physics    Nur Physik-Node"
	@echo "  make run-visualizer Nur Visualisierung"
	@echo "  make run-training   Nur Training"
	@echo ""
	@echo "  make shell          Shell im Container öffnen"
	@echo "  make logs           Logs aller Container"
	@echo "  make stop           Alle Container stoppen"
	@echo "  make clean          Container & Images entfernen"
	@echo "  make rebuild        Sauber neu bauen"
	@echo ""

# ── Basis-Image herunterladen ─────────────────────────────────
pull:
	@echo "📥  ROS2 Jazzy Desktop Image herunterladen..."
	docker pull osrf/ros:jazzy-desktop-full

# ── Docker-Image bauen ────────────────────────────────────────
build:
	@echo "🔨  Baue Simulation-Image..."
	$(COMPOSE) build

# ── X11 einrichten + bauen ────────────────────────────────────
setup:
	@bash scripts/setup_x11.sh
	@$(MAKE) build

# ── Alle Nodes (All-in-One mit tmux) ─────────────────────────
run-all: _x11_check
	@echo "🚀  Starte alle Nodes..."
	$(COMPOSE) run --rm sim

# ── Einzelne Nodes ───────────────────────────────────────────
run-physics:
	@echo "⚙️   Starte Physik-Node..."
	$(COMPOSE) run --rm physics

run-visualizer: _x11_check
	@echo "📡  Starte Visualizer..."
	$(COMPOSE) run --rm visualizer

run-training:
	@echo "🧠  Starte Training..."
	$(COMPOSE) run --rm training

# ── Shell im Container ────────────────────────────────────────
shell:
	@echo "🐚  Container-Shell öffnen..."
	docker run --rm -it \
	    -e DISPLAY=$(DISPLAY) \
	    -e ROS_DOMAIN_ID=42 \
	    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
	    -v $(PWD)/models:/ros2_ws/models \
	    --network host \
	    $(IMAGE) bash

# ── Logs & Status ─────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f

stop:
	$(COMPOSE) down

# ── Aufräumen ─────────────────────────────────────────────────
clean:
	$(COMPOSE) down --rmi local --volumes --remove-orphans
	@echo "🗑️  Container und lokale Images entfernt."

rebuild: clean build

# ── Internes: X11 prüfen ─────────────────────────────────────
_x11_check:
	@if [ -z "$(DISPLAY)" ]; then \
	    echo "⚠️  DISPLAY nicht gesetzt. 'make setup' zuerst ausführen."; \
	    exit 1; \
	fi
