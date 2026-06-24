#!/bin/bash
# ============================================================
# setup_x11.sh — X11-Anzeige für Docker freischalten
#
# Ausführen auf dem HOST (nicht im Container!) bevor
# der Visualizer gestartet wird.
# ============================================================

echo "🖥️  X11-Zugriff für Docker konfigurieren..."

# Prüfen ob DISPLAY gesetzt ist
if [ -z "$DISPLAY" ]; then
    echo "⚠️  DISPLAY nicht gesetzt. Setze auf :0"
    export DISPLAY=:0
fi

# Lokale Docker-Verbindungen erlauben
xhost +local:docker

echo "✅  X11-Zugriff freigegeben für DISPLAY=$DISPLAY"
echo "   (Gilt bis zum Abmelden oder 'xhost -local:docker')"
