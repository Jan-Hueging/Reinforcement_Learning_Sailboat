import cv2
import numpy as np
import math
import time
from config import Config

class StandaloneVisualizer:
    def __init__(self):
        self.window_name = "Sailboat Radar (Design Sandbox)"
        cv2.namedWindow(self.window_name)

        # Dummy Sensorwerte
        self.x, self.y, self.theta, self.speed = 0.0, 0.0, 0.0, 2.5
        self.wind_speed, self.wind_angle = 5.0, math.radians(45)
        self.scale = 15.0
        self.current_rudder = math.radians(0.0)
        self.current_sail = math.radians(35.0)
        self.debug_true_wind_speed = 5.0
        self.debug_true_wind_angle = 0.0
        
        self.target_x = 40.0
        self.target_y = 30.0

        # Schieberegler Setup
        self.name_rudder = 'Ruder (-45 bis 45 Grad)'.rjust(30, ' ')
        self.name_sail   = 'Segel (0 bis 70 Grad)'.rjust(30, ' ')
        self.name_wspeed = 'Wind Speed (m/s)'.rjust(30, ' ')
        self.name_wangle = 'Wind Angle (Deg)'.rjust(28, ' ')

        cv2.createTrackbar(self.name_rudder, self.window_name, 45, 90, self.update_controls)
        cv2.createTrackbar(self.name_sail, self.window_name, 35, 70, self.update_controls)
        cv2.createTrackbar(self.name_wspeed, self.window_name, 5, 20, self.update_weather)
        cv2.createTrackbar(self.name_wangle, self.window_name, 0, 360, self.update_weather)

        print("🎨 Sandbox Visualizer gestartet! Ändere den Code in sandbox_ui.py um das Design anzupassen.")

    def update_controls(self, _):
        val_rudder = cv2.getTrackbarPos(self.name_rudder, self.window_name)
        val_sail = cv2.getTrackbarPos(self.name_sail, self.window_name)
        self.current_rudder = math.radians(val_rudder - 45.0)
        self.current_sail = math.radians(float(val_sail))

    def update_weather(self, _):
        w_speed = float(cv2.getTrackbarPos(self.name_wspeed, self.window_name))
        w_angle_deg = float(cv2.getTrackbarPos(self.name_wangle, self.window_name))
        self.debug_true_wind_speed = w_speed
        self.debug_true_wind_angle = math.radians(w_angle_deg)
        self.wind_speed = w_speed
        self.wind_angle = self.debug_true_wind_angle

    def simulate_dummy_physics(self):
        # Ganz simple Fake-Physik, damit sich das Boot ein bisschen bewegt
        self.theta += self.current_rudder * -0.05
        self.x += math.cos(self.theta) * self.speed * 0.1
        self.y += math.sin(self.theta) * self.speed * 0.1

    def render_loop(self):
        WIDTH, HEIGHT = 1000, 1000
        # Wasser-Hintergrund (Tiefblau)
        img = np.full((HEIGHT, WIDTH, 3), (60, 30, 10), dtype=np.uint8)
        cx, cy = int(WIDTH * 0.15), HEIGHT // 2
        
        # Gitternetz (Ozean-Grid)
        for i in range(0, WIDTH, 50):
            cv2.line(img, (i, 0), (i, HEIGHT), (80, 45, 20), 1)
            cv2.line(img, (0, i), (WIDTH, i), (80, 45, 20), 1)
        
        # Umrechnung Boot-Position
        self.scale = 20.0
        px = int(cx + self.x * self.scale) % WIDTH
        py = int(cy - self.y * self.scale) % HEIGHT

        # Zielpunkt
        t_px = int(cx + self.target_x * self.scale) % WIDTH
        t_py = int(cy - self.target_y * self.scale) % HEIGHT
        
        # Ziel-Marker
        cv2.circle(img, (t_px, t_py), 12, (0, 165, 255), -1) 
        cv2.circle(img, (t_px, t_py), 16, (0, 255, 255), 2)  
        cv2.putText(img, f"TARGET", (t_px - 25, t_py - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        # ==========================================
        # Jollen-Design 
        # ==========================================
        L = 60.0  # Länge
        W = 24.0  # Breite

        # 1. Rumpf-Umriss (geschwungen, breites Heck, spitzer Bug)
        hull_rel_pts = [
            (L/2, 0),                 # Bugspitze
            (L*0.25, W/2),            # Bugreling Backbord
            (-L*0.3, W/2 * 0.95),     # Mitte Backbord
            (-L/2, W/2 * 0.7),        # Heck Ecke Backbord
            (-L/2 * 1.05, 0),         # Heck Mitte (leicht konvex)
            (-L/2, -W/2 * 0.7),       # Heck Ecke Steuerbord
            (-L*0.3, -W/2 * 0.95),    # Mitte Steuerbord
            (L*0.25, -W/2),           # Bugreling Steuerbord
        ]

        def transform_pts(rel_pts):
            pts = []
            for x, y in rel_pts:
                rx = px + x * math.cos(self.theta) - y * math.sin(self.theta)
                ry = py - (x * math.sin(self.theta) + y * math.cos(self.theta))
                pts.append([int(rx), int(ry)])
            return np.array(pts, np.int32)

        boat_pts = transform_pts(hull_rel_pts)

        # Rumpf zeichnen (Weiß mit schwarzer Outline)
        cv2.fillConvexPoly(img, boat_pts, (245, 245, 245))
        cv2.polylines(img, [boat_pts], True, (20, 20, 20), 2)

        # 2. Cockpit (die innere Öffnung)
        cockpit_rel_pts = [
            (L*0.1, W/2 * 0.65),      # Vorne Backbord
            (-L*0.3, W/2 * 0.65),     # Hinten Backbord
            (-L*0.42, W/2 * 0.4),     # Heck-Ecke Backbord
            (-L*0.42, -W/2 * 0.4),    # Heck-Ecke Steuerbord
            (-L*0.3, -W/2 * 0.65),    # Hinten Steuerbord
            (L*0.1, -W/2 * 0.65),     # Vorne Steuerbord
        ]
        cockpit_pts = transform_pts(cockpit_rel_pts)
        
        # Cockpit zeichnen (Grauer Boden, dünne Outline)
        cv2.fillConvexPoly(img, cockpit_pts, (150, 150, 150))
        cv2.polylines(img, [cockpit_pts], True, (100, 100, 100), 1)

        # 3. Mastloch (auf dem Deck vor dem Cockpit)
        mast_x = int(px + (L * 0.25) * math.cos(self.theta))
        mast_y = int(py - (L * 0.25) * math.sin(self.theta))
        cv2.circle(img, (mast_x, mast_y), 3, (40, 40, 40), 2)

        # ==========================================
        # Dynamische Teile (Ruder & Segel)
        # ==========================================

        # Ruder (Pinne am Heck)
        stern_x = int(px - math.cos(self.theta) * (L/2 * 1.05))
        stern_y = int(py + math.sin(self.theta) * (L/2 * 1.05))
        rudder_angle = self.theta + self.current_rudder
        rudder_end_x = int(stern_x - math.cos(rudder_angle) * 20)
        rudder_end_y = int(stern_y + math.sin(rudder_angle) * 20)
        # Pinne (Holzfarben/Rot)
        cv2.line(img, (stern_x, stern_y), (rudder_end_x, rudder_end_y), (30, 30, 200), 3)

        # Segel (Weiß, leicht gebogen wirkend durch dicke Linie)
        actual_sail_rad = math.copysign(self.current_sail, self.wind_angle)
        sail_angle_global = self.theta + math.pi + actual_sail_rad
        sail_end_x = int(mast_x + math.cos(sail_angle_global) * 45)
        sail_end_y = int(mast_y - math.sin(sail_angle_global) * 45)
        cv2.line(img, (mast_x, mast_y), (sail_end_x, sail_end_y), (250, 250, 250), 4)

        # HUD / Telemetrie
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (250, 140), (0, 0, 0), -1)
        cv2.rectangle(overlay, (10, 150), (250, 280), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        
        cv2.putText(img, "TELEMETRY", (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "-" * 30, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(img, f"Speed: {self.speed:.2f} m/s", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
        
        # Wind Indikator
        compass_cx, compass_cy = WIDTH - 80, 80
        cv2.circle(img, (compass_cx, compass_cy), 40, (30, 30, 30), -1)
        cv2.circle(img, (compass_cx, compass_cy), 40, (100, 100, 100), 2)
        cv2.putText(img, "N", (compass_cx - 5, compass_cy - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
        
        tw_end_x = int(compass_cx - math.cos(self.debug_true_wind_angle) * 30)
        tw_end_y = int(compass_cy + math.sin(self.debug_true_wind_angle) * 30)
        cv2.arrowedLine(img, (compass_cx, compass_cy), (tw_end_x, tw_end_y), (255, 150, 0), 3, tipLength=0.3)

        cv2.imshow(self.window_name, img)
        return cv2.waitKey(30)

def main():
    sim = StandaloneVisualizer()
    while True:
        sim.simulate_dummy_physics()
        key = sim.render_loop()
        if key == 27: # ESC Taste
            break
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
