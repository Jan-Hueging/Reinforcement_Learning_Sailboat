# ROS2 Schnittstellen-Spezifikation für Gazebo

Dieses Dokument beschreibt exakt, welche ROS2-Topics und Services deine Gazebo-Simulation bereitstellen muss, um als Physik-Engine für das Reinforcement Learning (RL) Boot zu fungieren.

> [!IMPORTANT]
> **Netzwerk-Voraussetzungen:**
> * Die Gazebo-Simulation muss zwingend auf der `ROS_DOMAIN_ID=42` laufen.
> * Wenn das Training im Docker läuft, muss `network_mode: "host"` in der `docker-compose.yml` gesetzt sein.
> * Beide Rechner müssen im selben Netzwerk sein und die Firewall darf UDP-Multicast nicht blockieren.

---

## 1. Sensordaten: Gazebo ➡️ KI (Gazebo publisht, KI lauscht)

Die folgenden Topics müssen **von Gazebo** gesendet werden. Das RL-Skript erwartet diese Daten, um den Zustand der Welt zu erfassen.

| Topic-Name | Nachrichtentyp | Einheit | Beschreibung & Referenzsystem |
| :--- | :--- | :--- | :--- |
| `/GPS` | `geometry_msgs/msg/Point` | Meter (m) | **Lokale X/Y Position** des Bootes in der Welt. NWU-Frame: `+x` = Norden, `-y` = Osten (bzw. `+y` = Westen). Startpunkt (0,0). `z` kann `0.0` bleiben. |
| `/Kompass` | `std_msgs/msg/Float64` | Radiant (rad) | **Ausrichtung (Heading)** des Bootes in der Welt. `0` = Norden (+X), `+π/2` = Westen (+Y), `-π/2` = Osten (-Y), `±π` = Süden (-X). |
| `/Neigung` | `std_msgs/msg/Float64` | Radiant (rad) | **Krängung / Rollwinkel** des Bootes (seitliche Neigung durch Winddruck). |
| `/Ruderstellung_Ist` | `std_msgs/msg/Float64` | Radiant (rad) | **Aktueller Winkel** des Ruderblatts. |
| `/Segelstellung_Ist` | `std_msgs/msg/Float64` | Radiant (rad) | **Aktuelle Segelstellung** (bzw. Schotlänge). |
| `/Windgeschwindigkeit`| `std_msgs/msg/Float64` | m/s | **Scheinbarer Wind (Speed)**. Die Stärke des Windes, den das Boot spürt (inkl. Fahrtwind). |
| `/Windrichtung` | `std_msgs/msg/Float64` | Radiant (rad) | **Scheinbarer Wind (Richtung)**. Relativer Winkel zur *Bootsnase*. `0` = Gegenwind (von vorne), `+π/2` = von rechts, `-π/2` = von links. |

> [!TIP]
> Falls dein Gazebo echte GPS-Koordinaten in WGS84 liefert, musst du diese für das Topic `/GPS` über eine Äquirektangularprojektion (oder via `navsat_transform_node`) in ein lokales Meter-Koordinatensystem (X,Y) umrechnen! Alternativ kannst du direkt die Ground-Truth (Odometrie) aus Gazebo nutzen.

---

## 2. Steuerbefehle: KI ➡️ Gazebo (KI publisht, Gazebo lauscht)

Die folgenden Topics werden **vom RL-Training** gesendet. Deine Gazebo-Simulation muss diese abonnieren und die Aktuatoren des Bootes entsprechend bewegen.

| Topic-Name | Nachrichtentyp | Einheit | Beschreibung |
| :--- | :--- | :--- | :--- |
| `/Ruderstellung_Soll`| `std_msgs/msg/Float64` | Radiant (rad) | **Zielwinkel für das Ruder**. Die KI möchte, dass Gazebo das Ruder auf diesen Winkel stellt. |
| `/Segelstellung_Soll`| `std_msgs/msg/Float64` | Radiant (rad) | **Zielwinkel für das Segel**. Die KI möchte, dass die Schot/das Segel auf diesen Winkel gefiert oder dichtgeholt wird. |

> [!NOTE]
> Die KI verlangt keine schlagartige Änderung, sondern gibt einen Sollwert vor. Es ist Aufgabe deiner Gazebo-Plugins (z.B. PID-Controller für die Winden/Servos), diese Winkel anzufahren.

---

## 3. Zwingend benötigte Services: Gazebo ➡️ KI

Damit das Reinforcement Learning funktioniert, muss die Simulation in der Lage sein, sich bei Bedarf (z. B. wenn das Ziel erreicht wurde) auf den Ursprungszustand zurückzusetzen.

| Service-Name | Service-Typ | Beschreibung |
| :--- | :--- | :--- |
| (Keine) | - | Da die KI nun kontinuierlich lernt (Continuous RL), wird das Boot niemals von der KI zurückgesetzt. Gazebo läuft einfach unendlich weiter. |


---

## 4. (Optional) Feedback der KI: KI ➡️ Gazebo

| Topic-Name | Nachrichtentyp | Einheit | Beschreibung |
| :--- | :--- | :--- | :--- |
| `/navigation/target` | `geometry_msgs/msg/Vector3` | Meter (m) | Das aktuell ausgewürfelte **Ziel** der KI. `x` und `y` entsprechen den Zielkoordinaten, `z` ist `0`. |
