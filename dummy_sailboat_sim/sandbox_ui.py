import cv2
import numpy as np
import math
import time
from config import Config

class StandaloneVisualizer:
    def __init__(self):
        self.window_name = "Sailboat Radar (Design Sandbox)"
        cv2.namedWindow(self.window_name)

        # Lade das generierte Boot
        import os
        img_path = 'dummy_sailboat_sim/boot.png'
        if os.path.exists(img_path):
            self.boat_sprite = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if self.boat_sprite is not None and self.boat_sprite.shape[2] == 3:
                self.boat_sprite = cv2.cvtColor(self.boat_sprite, cv2.COLOR_BGR2BGRA)
                white_mask = np.all(self.boat_sprite[:, :, :3] >= 240, axis=2)
                self.boat_sprite[white_mask, 3] = 0
            if self.boat_sprite is not None:
                self.boat_sprite = cv2.rotate(self.boat_sprite, cv2.ROTATE_90_CLOCKWISE)
                self.boat_sprite = cv2.resize(self.boat_sprite, (90, 45))
        else:
            self.boat_sprite = None
            
        # Lade Wind-Icon und schneide den schwarzen Hintergrund absolut sauber aus
        wind_path = 'dummy_sailboat_sim/wind_icon.png'
        if os.path.exists(wind_path):
            self.wind_sprite = cv2.imread(wind_path, cv2.IMREAD_COLOR)
            if self.wind_sprite is not None:
                gray = cv2.cvtColor(self.wind_sprite, cv2.COLOR_BGR2GRAY)
                # Verbessertes Alpha-Blending: Alles unter Helligkeit 40 wird komplett 0 (transparent)
                # Alles darüber wird weich nach oben skaliert, um saubere Ränder zu behalten.
                alpha_channel = np.clip((gray.astype(np.int16) - 40) * (255 / 215), 0, 255).astype(np.uint8)
                b, g, r = 255, 255, 255
                self.wind_sprite = cv2.merge([np.full_like(gray, b), np.full_like(gray, g), np.full_like(gray, r), alpha_channel])
                self.wind_sprite = cv2.resize(self.wind_sprite, (75, 75), interpolation=cv2.INTER_AREA)
        else:
            self.wind_sprite = None

        # Dummy Sensorwerte
        self.x, self.y, self.theta, self.speed = 0.0, 0.0, 0.0, 2.5
        self.wind_speed, self.wind_angle = 5.0, math.radians(45)
        self.scale = 15.0
        self.current_rudder = math.radians(0.0)
        self.current_sail = math.radians(35.0)
        self.debug_true_wind_speed = 5.0
        self.debug_true_wind_angle = 0.0
        
        import random
        self.target_x = random.uniform(10.0, 80.0)
        self.target_y = random.uniform(-30.0, 30.0)

        # Eigene, moderne Schieberegler (On-Screen Overlay)
        self.WIDTH, self.HEIGHT = 1000, 660
        self.slider_rudder_val = 45 # 0..90
        self.slider_sail_val = 35   # 0..70
        self.dragging_rudder = False
        self.dragging_sail = False

        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from dummy_sailboat_sim.reward_calculator import RewardCalculator
        self.reward_calc = RewardCalculator()
        self.prev_dist = 0.0
        
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        print("Sandbox Visualizer gestartet! Aendere den Code in sandbox_ui.py um das Design anzupassen.")

    def mouse_callback(self, event, x, y, flags, param):
        rudder_rect = (550, self.HEIGHT - 120, 350, 15)
        sail_rect   = (550, self.HEIGHT - 60, 350, 15)
        
        def get_val(rect, max_val):
            rx, ry, rw, rh = rect
            if rx <= x <= rx + rw:
                return int(max(0.0, min(1.0, (x - rx) / rw)) * max_val)
            elif x < rx: return 0
            else: return max_val
            
        def hit(rect):
            rx, ry, rw, rh = rect
            return rx - 20 <= x <= rx + rw + 20 and ry - 15 <= y <= ry + rh + 15

        if event == cv2.EVENT_LBUTTONDOWN:
            if hit(rudder_rect):
                self.slider_rudder_val = get_val(rudder_rect, 90)
                self.dragging_rudder = True
            elif hit(sail_rect):
                self.slider_sail_val = get_val(sail_rect, 70)
                self.dragging_sail = True
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging_rudder: self.slider_rudder_val = get_val(rudder_rect, 90)
            if self.dragging_sail: self.slider_sail_val = get_val(sail_rect, 70)
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_rudder = False
            self.dragging_sail = False

        self.current_rudder = math.radians(self.slider_rudder_val - 45.0)
        self.current_sail = math.radians(self.slider_sail_val)



    def simulate_dummy_physics(self):
        # Ganz simple Fake-Physik, damit sich das Boot ein bisschen bewegt
        self.theta += self.current_rudder * -0.05
        self.x += math.cos(self.theta) * self.speed * 0.1
        self.y += math.sin(self.theta) * self.speed * 0.1
        
        # Wind langsam drehen lassen (für Testzwecke)
        self.debug_true_wind_angle += 0.02
        self.debug_true_wind_angle %= (2 * math.pi)
        self.wind_angle = self.debug_true_wind_angle
        
        # Ziel-Kollision prüfen und neu spawnen (wie im RL-Training)
        dist_to_target = math.hypot(self.target_x - self.x, self.target_y - self.y)
        
        # REWARD BERECHNUNG FÜR LOG
        state_dict = {
            'pos_x': self.x,
            'pos_y': self.y,
            'current_dist': dist_to_target,
            'prev_dist': getattr(self, 'prev_dist', dist_to_target),
            'v_linear': self.speed,
            'angle_to_target': 0.0,
            'heel_angle': 0.0
        }
        self.reward_calc.calculate(state_dict, [0.0, 0.0]) # Aktionen simulieren wir mal mit 0
        self.prev_dist = dist_to_target

        if dist_to_target < 5.0:  # 5 Meter Radius
            import random
            self.target_x = random.uniform(10.0, 80.0)
            self.target_y = random.uniform(-30.0, 30.0)

    def render_loop(self):
        WIDTH, HEIGHT = self.WIDTH, self.HEIGHT
        # Wasser-Hintergrund (Tiefblau)
        img = np.full((HEIGHT, WIDTH, 3), (60, 30, 10), dtype=np.uint8)
        cx, cy = int(WIDTH * 0.15), HEIGHT // 2
        
        # Umrechnung Boot-Position & Zoom (10.0 = 4x so viel Fläche sichtbar wie vorher)
        self.scale = 10.0
        
        # Gitternetz (Ozean-Grid - 10 Meter Raster in der echten Welt)
        grid_step = max(10, int(10 * self.scale))
        for i in range(0, max(WIDTH, HEIGHT), grid_step):
            if i < WIDTH:
                cv2.line(img, (i, 0), (i, HEIGHT), (80, 45, 20), 1)
            if i < HEIGHT:
                cv2.line(img, (0, i), (WIDTH, i), (80, 45, 20), 1)
        
        px = int(cx + self.x * self.scale) % WIDTH
        py = int(cy - self.y * self.scale) % HEIGHT

        # Zielpunkt
        t_px = int(cx + self.target_x * self.scale) % WIDTH
        t_py = int(cy - self.target_y * self.scale) % HEIGHT
        
        # 1. Führungslinie vom Boot zum Ziel (gestrichelt)
        dist = math.hypot(t_px - px, t_py - py)
        if dist > 0:
            dx, dy = (t_px - px)/dist, (t_py - py)/dist
            dash_len = 10
            for i in range(0, int(dist), dash_len * 2):
                p1 = (int(px + dx * i), int(py + dy * i))
                p2_dist = min(i + dash_len, int(dist))
                p2 = (int(px + dx * p2_dist), int(py + dy * p2_dist))
                cv2.line(img, p1, p2, (100, 100, 100), 1, cv2.LINE_AA)
        
        # 2. Moderner Ziel-Marker (Dunkelgrau)
        target_color = (160, 160, 160) # Modernes helles Grau für besseren Kontrast auf Dunkelblau
        
        # Zielflagge statt eines einfachen Punktes
        # Fahnenmast
        cv2.line(img, (t_px, t_py), (t_px, t_py - 16), target_color, 2, cv2.LINE_AA)
        
        # Schachbrett-Muster (Zielflagge)
        flag_w, flag_h = 4, 4
        start_x, start_y = t_px + 1, t_py - 16
        for row in range(3):
            for col in range(4):
                color = (250, 250, 250) if (row + col) % 2 == 0 else (30, 30, 30)
                pt1 = (start_x + col * flag_w, start_y + row * flag_h)
                pt2 = (start_x + (col + 1) * flag_w, start_y + (row + 1) * flag_h)
                cv2.rectangle(img, pt1, pt2, color, -1)
                
        # Zarte Umrandung um die Fahne für mehr Kontrast
        cv2.rectangle(img, (start_x, start_y), (start_x + 4 * flag_w, start_y + 3 * flag_h), target_color, 1)
        # Kleiner Sockelpunkt unten am Mast, um exakt die Mitte zu markieren
        cv2.circle(img, (t_px, t_py), 2, target_color, -1, cv2.LINE_AA)
        
        # 3 Distanz-Ringe basierend auf dem echten Radius (1m und 5m)
        r_1m = int(1.0 * self.scale)
        r_5m = int(5.0 * self.scale)
        
        cv2.circle(img, (t_px, t_py), r_1m, target_color, 1, cv2.LINE_AA)
        cv2.circle(img, (t_px, t_py), r_5m, target_color, 1, cv2.LINE_AA)
        
        # Ziel-Beschriftung & Ring-Labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "TARGET", (t_px + r_1m + 5, t_py - 5), font, 0.45, target_color, 1, cv2.LINE_AA)
        
        # Labels für die Radien (leicht versetzt auf den Linien)
        cv2.putText(img, "1m", (t_px + 2, t_py - r_1m - 4), font, 0.35, target_color, 1, cv2.LINE_AA)
        cv2.putText(img, "5m", (t_px + 2, t_py - r_5m - 4), font, 0.35, target_color, 1, cv2.LINE_AA)

        # ==========================================
        # Jollen-Design 
        # ==========================================
        L = 4.5 * self.scale  # Länge (4.5 Meter, 50% größer)
        W = 1.8 * self.scale  # Breite (1.8 Meter, 50% größer)

        # 1. Rumpf-Umriss (geschwungen, breites Heck, abgerundeter Bug)
        hull_rel_pts = [
            (L*0.46, W*0.18),         # Bug Backbord
            (L*0.5, 0),               # Bug Mitte (abgerundet)
            (L*0.46, -W*0.18),        # Bug Steuerbord
            (L*0.25, -W/2),           # Bugreling Steuerbord
            (-L*0.3, -W/2 * 0.95),    # Mitte Steuerbord
            (-L/2, -W/2 * 0.7),       # Heck Ecke Steuerbord
            (-L/2 * 1.05, 0),         # Heck Mitte (leicht konvex)
            (-L/2, W/2 * 0.7),        # Heck Ecke Backbord
            (-L*0.3, W/2 * 0.95),     # Mitte Backbord
            (L*0.25, W/2),            # Bugreling Backbord
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

        # 3. Mastloch (weiter hinten, nicht ganz mittig)
        mast_offset = L * 0.15
        mast_x = int(px + mast_offset * math.cos(self.theta))
        mast_y = int(py - mast_offset * math.sin(self.theta))
        cv2.circle(img, (mast_x, mast_y), 3, (40, 40, 40), 2)

        # ==========================================
        # Dynamische Teile (Ruder & Segel)
        # ==========================================

        # Ruder (Pinne am Heck)
        stern_x = int(px - math.cos(self.theta) * (L/2 * 1.05))
        stern_y = int(py + math.sin(self.theta) * (L/2 * 1.05))
        rudder_angle = self.theta + self.current_rudder
        rudder_end_x = int(stern_x - math.cos(rudder_angle) * (1.1 * self.scale))
        rudder_end_y = int(stern_y + math.sin(rudder_angle) * (1.1 * self.scale))
        # Pinne (Holzfarben/Rot)
        cv2.line(img, (stern_x, stern_y), (rudder_end_x, rudder_end_y), (30, 30, 200), 3)

        # Segel (Weiß, leicht gebogen wirkend durch dicke Linie)
        actual_sail_rad = math.copysign(self.current_sail, self.wind_angle)
        sail_angle_global = self.theta + math.pi + actual_sail_rad
        sail_end_x = int(mast_x + math.cos(sail_angle_global) * (2.55 * self.scale))
        sail_end_y = int(mast_y - math.sin(sail_angle_global) * (2.55 * self.scale))
        cv2.line(img, (mast_x, mast_y), (sail_end_x, sail_end_y), (250, 250, 250), 4)

        # HUD / Telemetrie
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (250, 140), (0, 0, 0), -1)
        # Neues HUD für den REWARD LOG
        cv2.rectangle(overlay, (10, 150), (250, 320), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        
        cv2.putText(img, "TELEMETRY", (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "-" * 30, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(img, f"Speed: {self.speed:.2f} m/s", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
        
        # Reward Log Texte
        cv2.putText(img, "REWARD LOG", (20, 175), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "-" * 30, (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        breakdown = self.reward_calc.latest_breakdown
        cv2.putText(img, f"VMG:    {breakdown.get('VMG', 0.0):+8.4f}", (20, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(img, f"Jitter: {breakdown.get('Jitter', 0.0):+8.4f}", (20, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(img, f"Time:   {breakdown.get('Time', 0.0):+8.4f}", (20, 255), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(img, f"Heel:   {breakdown.get('Heel', 0.0):+8.4f}", (20, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(img, f"TOTAL:  {breakdown.get('Total', 0.0):+8.4f}", (20, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
        
        # ==========================================
        # Moderner Wind-Indikator (Uhr-Style, transparent)
        # ==========================================
        compass_cx, compass_cy = WIDTH - 90, 90
        compass_r = 75
        
        # 1. Außenring (Weiß, komplett transparenter Hintergrund)
        cv2.circle(img, (compass_cx, compass_cy), compass_r, (255, 255, 255), 2, cv2.LINE_AA)
        
        # 2. Striche nach innen (wie bei einer Uhr) & Himmelsrichtungen
        font = cv2.FONT_HERSHEY_DUPLEX
        for angle_deg in range(0, 360, 30):
            rad = math.radians(angle_deg - 90)
            
            x_outer = int(compass_cx + math.cos(rad) * compass_r)
            y_outer = int(compass_cy + math.sin(rad) * compass_r)
            
            if angle_deg % 90 == 0:
                # Haupt-Himmelsrichtungen: Lange Striche
                x_inner = int(compass_cx + math.cos(rad) * (compass_r * 0.82))
                y_inner = int(compass_cy + math.sin(rad) * (compass_r * 0.82))
                cv2.line(img, (x_outer, y_outer), (x_inner, y_inner), (255, 255, 255), 2, cv2.LINE_AA)
                
                # Buchstaben weiter innen platzieren
                if angle_deg == 0:
                    cv2.putText(img, "N", (compass_cx - 6, compass_cy - int(compass_r*0.55)), font, 0.55, (60, 60, 255), 1, cv2.LINE_AA)
                elif angle_deg == 90:
                    cv2.putText(img, "E", (compass_cx + int(compass_r*0.55) - 6, compass_cy + 6), font, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
                elif angle_deg == 180:
                    cv2.putText(img, "S", (compass_cx - 6, compass_cy + int(compass_r*0.55) + 6), font, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
                elif angle_deg == 270:
                    cv2.putText(img, "W", (compass_cx - int(compass_r*0.55) - 12, compass_cy + 6), font, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                # Normale Striche: Deutlich kürzer
                x_inner = int(compass_cx + math.cos(rad) * (compass_r * 0.92))
                y_inner = int(compass_cy + math.sin(rad) * (compass_r * 0.92))
                cv2.line(img, (x_outer, y_outer), (x_inner, y_inner), (255, 255, 255), 2, cv2.LINE_AA)

        # 3. Wind-Icon in der Mitte zeichnen (statt Wellenlinien)
        if hasattr(self, 'wind_sprite') and self.wind_sprite is not None:
            # -angle_deg, da OpenCV im Uhrzeigersinn rotiert und Y nach unten zeigt
            angle_deg = math.degrees(self.debug_true_wind_angle)
            center = (self.wind_sprite.shape[1]//2, self.wind_sprite.shape[0]//2)
            rot_mat = cv2.getRotationMatrix2D(center, -angle_deg, 1.0)
            
            h, w = self.wind_sprite.shape[:2]
            rotated_wind = cv2.warpAffine(self.wind_sprite, rot_mat, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
            
            top_left_x = int(compass_cx - w/2)
            top_left_y = int(compass_cy - h/2)
            
            y1, y2 = max(0, top_left_y), min(HEIGHT, top_left_y + h)
            x1, x2 = max(0, top_left_x), min(WIDTH, top_left_x + w)
            y1o, y2o = max(0, -top_left_y), min(h, HEIGHT - top_left_y)
            x1o, x2o = max(0, -top_left_x), min(w, WIDTH - top_left_x)

            if y1 < y2 and x1 < x2:
                alpha_s = rotated_wind[y1o:y2o, x1o:x2o, 3] / 255.0
                alpha_l = 1.0 - alpha_s
                for c in range(3):
                    img[y1:y2, x1:x2, c] = (alpha_s * rotated_wind[y1o:y2o, x1o:x2o, c] +
                                            alpha_l * img[y1:y2, x1:x2, c])

        # ==========================================
        # Moderne On-Screen Regler zeichnen
        # ==========================================
        def draw_slider(img, text, rect, val, max_val, disp_val, suffix=""):
            rx, ry, rw, rh = rect
            # Hintergrund-Box
            cv2.rectangle(img, (rx - 150, ry - 15), (rx + rw + 20, ry + rh + 15), (20, 20, 25), -1)
            cv2.rectangle(img, (rx - 150, ry - 15), (rx + rw + 20, ry + rh + 15), (80, 80, 80), 1)
            # Track
            cv2.rectangle(img, (rx, ry + rh//2 - 2), (rx + rw, ry + rh//2 + 2), (60, 60, 60), -1)
            # Active Track
            k_x = rx + int((val / max_val) * rw)
            cv2.rectangle(img, (rx, ry + rh//2 - 2), (k_x, ry + rh//2 + 2), (0, 200, 255), -1)
            # Knob
            cv2.circle(img, (k_x, ry + rh//2), 10, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(img, (k_x, ry + rh//2), 10, (100, 100, 100), 1, cv2.LINE_AA)
            # Label
            label = f"{text}: {disp_val}{suffix}"
            cv2.putText(img, label, (rx - 130, ry + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        draw_slider(img, "Ruder", (550, HEIGHT - 120, 350, 15), self.slider_rudder_val, 90, self.slider_rudder_val - 45, " Grad")
        draw_slider(img, "Segel", (550, HEIGHT - 60, 350, 15), self.slider_sail_val, 70, self.slider_sail_val, " Grad")

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
