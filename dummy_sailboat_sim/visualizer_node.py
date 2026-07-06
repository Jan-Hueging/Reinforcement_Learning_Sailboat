import rclpy
from rclpy.node import Node
import cv2
import numpy as np
import math
import os

from std_msgs.msg import Float64
from geometry_msgs.msg import Point, Vector3
from dummy_sailboat_sim.config import Config

class VisualizerNode(Node):
    def __init__(self):
        super().__init__('visualizer_node')

        self.window_name = "Sailboat Radar (God-Mode)"
        cv2.namedWindow(self.window_name)

        self.x, self.y, self.theta, self.speed = 0.0, 0.0, 0.0, 0.0
        self.wind_speed, self.wind_angle = 0.0, 0.0
        self.current_rudder = math.radians(Config.INITIAL_RUDDER_ANGLE_DEG)
        self.current_sail = math.radians(Config.INITIAL_SAIL_ANGLE_DEG)
        self.debug_true_wind_speed = 5.0
        self.debug_true_wind_angle = 0.0

        # Lade Wind-Icon
        wind_path = 'dummy_sailboat_sim/wind_icon.png'
        if os.path.exists(wind_path):
            self.wind_sprite = cv2.imread(wind_path, cv2.IMREAD_COLOR)
            if self.wind_sprite is not None:
                gray = cv2.cvtColor(self.wind_sprite, cv2.COLOR_BGR2GRAY)
                alpha_channel = np.clip((gray.astype(np.int16) - 40) * (255 / 215), 0, 255).astype(np.uint8)
                b, g, r = 255, 255, 255
                self.wind_sprite = cv2.merge([np.full_like(gray, b), np.full_like(gray, g), np.full_like(gray, r), alpha_channel])
                self.wind_sprite = cv2.resize(self.wind_sprite, (75, 75), interpolation=cv2.INTER_AREA)
        else:
            self.wind_sprite = None

        # Publisher für die Steuerung
        self.pub_rudder = self.create_publisher(Float64, Config.TOPIC_RUDDER_SOLL, 10)
        self.pub_sail = self.create_publisher(Float64, Config.TOPIC_SAIL_SOLL, 10)
        self.pub_weather = self.create_publisher(Vector3, '/debug/true_wind', 10)

        # Subscriber für die Sensoren
        self.create_subscription(Point, Config.TOPIC_GPS, self.gps_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_COMPASS, self.compass_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_WIND_SPEED, self.wind_speed_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_WIND_DIR, self.wind_dir_cb, 10)

        # Eigene, moderne Schieberegler (On-Screen Overlay)
        self.WIDTH, self.HEIGHT = 1000, 1000
        self.slider_rudder_val = 45 # 0..90
        self.slider_sail_val = 35   # 0..70
        self.slider_wspeed_val = 5  # 0..20
        self.slider_wangle_val = 0  # 0..360
        self.dragging_rudder = False
        self.dragging_sail = False
        self.dragging_wspeed = False
        self.dragging_wangle = False
        
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        self.create_timer(1.0 / 30.0, self.render_loop)
        self.get_logger().info('Radar hochgefahren! Fenster sollte offen sein.')

        # Speicher für das dynamische Ziel
        self.target_x = 0.0
        self.target_y = 0.0

        # Subscriber Ruder, Segel & Ziel
        self.create_subscription(Vector3, '/navigation/target', self.target_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_RUDDER_IST, self.cmd_rudder_cb, 10)
        self.create_subscription(Float64, Config.TOPIC_SAIL_IST, self.cmd_sail_cb, 10)

    def mouse_callback(self, event, x, y, flags, param):
        rudder_rect = (550, self.HEIGHT - 240, 350, 15)
        sail_rect   = (550, self.HEIGHT - 180, 350, 15)
        wspeed_rect = (550, self.HEIGHT - 120, 350, 15)
        wangle_rect = (550, self.HEIGHT - 60,  350, 15)
        
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
            elif hit(wspeed_rect):
                self.slider_wspeed_val = get_val(wspeed_rect, 20)
                self.dragging_wspeed = True
            elif hit(wangle_rect):
                self.slider_wangle_val = get_val(wangle_rect, 360)
                self.dragging_wangle = True
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging_rudder: self.slider_rudder_val = get_val(rudder_rect, 90)
            if self.dragging_sail: self.slider_sail_val = get_val(sail_rect, 70)
            if self.dragging_wspeed: self.slider_wspeed_val = get_val(wspeed_rect, 20)
            if self.dragging_wangle: self.slider_wangle_val = get_val(wangle_rect, 360)
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_rudder = False
            self.dragging_sail = False
            self.dragging_wspeed = False
            self.dragging_wangle = False

        if self.dragging_rudder or self.dragging_sail:
            rudder_deg = self.slider_rudder_val - 45.0
            sail_deg = float(self.slider_sail_val)
            self.pub_rudder.publish(Float64(data=rudder_deg))
            self.pub_sail.publish(Float64(data=sail_deg))
            
        if self.dragging_wspeed or self.dragging_wangle:
            w_speed = float(self.slider_wspeed_val)
            w_angle_rad = math.radians(float(self.slider_wangle_val))
            self.debug_true_wind_speed = w_speed
            self.debug_true_wind_angle = w_angle_rad
            self.pub_weather.publish(Vector3(x=w_speed, y=w_angle_rad, z=0.0))

    def gps_cb(self, msg):
        self.x = msg.x
        self.y = msg.y

    def compass_cb(self, msg):
        self.theta = msg.data

    def wind_speed_cb(self, msg):
        self.wind_speed = msg.data

    def wind_dir_cb(self, msg):
        self.wind_angle = msg.data

    def target_cb(self, msg):
        self.target_x = msg.x
        self.target_y = msg.y

    def cmd_rudder_cb(self, msg):
        self.current_rudder = math.radians(msg.data)

    def cmd_sail_cb(self, msg):
        self.current_sail = math.radians(msg.data)

    def render_loop(self):
        WIDTH, HEIGHT = self.WIDTH, self.HEIGHT
        img = np.full((HEIGHT, WIDTH, 3), (60, 30, 10), dtype=np.uint8)
        cx, cy = int(WIDTH * 0.15), HEIGHT // 2
        
        self.scale = 10.0
        grid_step = max(10, int(10 * self.scale))
        for i in range(0, max(WIDTH, HEIGHT), grid_step):
            if i < WIDTH: cv2.line(img, (i, 0), (i, HEIGHT), (80, 45, 20), 1)
            if i < HEIGHT: cv2.line(img, (0, i), (WIDTH, i), (80, 45, 20), 1)
        
        px = int(cx + self.x * self.scale) % WIDTH
        py = int(cy - self.y * self.scale) % HEIGHT
        t_px = int(cx + self.target_x * self.scale) % WIDTH
        t_py = int(cy - self.target_y * self.scale) % HEIGHT
        
        dist = math.hypot(t_px - px, t_py - py)
        if dist > 0:
            dx, dy = (t_px - px)/dist, (t_py - py)/dist
            dash_len = 10
            for i in range(0, int(dist), dash_len * 2):
                p1 = (int(px + dx * i), int(py + dy * i))
                p2_dist = min(i + dash_len, int(dist))
                p2 = (int(px + dx * p2_dist), int(py + dy * p2_dist))
                cv2.line(img, p1, p2, (100, 100, 100), 1, cv2.LINE_AA)
        
        target_color = (160, 160, 160)
        cv2.line(img, (t_px, t_py), (t_px, t_py - 16), target_color, 2, cv2.LINE_AA)
        flag_w, flag_h = 4, 4
        start_x, start_y = t_px + 1, t_py - 16
        for row in range(3):
            for col in range(4):
                color = (250, 250, 250) if (row + col) % 2 == 0 else (30, 30, 30)
                cv2.rectangle(img, (start_x + col * flag_w, start_y + row * flag_h), (start_x + (col + 1) * flag_w, start_y + (row + 1) * flag_h), color, -1)
        cv2.rectangle(img, (start_x, start_y), (start_x + 4 * flag_w, start_y + 3 * flag_h), target_color, 1)
        cv2.circle(img, (t_px, t_py), 2, target_color, -1, cv2.LINE_AA)
        
        r_1m = int(1.0 * self.scale)
        r_5m = int(5.0 * self.scale)
        cv2.circle(img, (t_px, t_py), r_1m, target_color, 1, cv2.LINE_AA)
        cv2.circle(img, (t_px, t_py), r_5m, target_color, 1, cv2.LINE_AA)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "TARGET", (t_px + r_1m + 5, t_py - 5), font, 0.45, target_color, 1, cv2.LINE_AA)
        cv2.putText(img, "1m", (t_px + 2, t_py - r_1m - 4), font, 0.35, target_color, 1, cv2.LINE_AA)
        cv2.putText(img, "5m", (t_px + 2, t_py - r_5m - 4), font, 0.35, target_color, 1, cv2.LINE_AA)

        L = 4.5 * self.scale
        W = 1.8 * self.scale

        hull_rel_pts = [
            (L*0.46, W*0.18), (L*0.5, 0), (L*0.46, -W*0.18),
            (L*0.25, -W/2), (-L*0.3, -W/2 * 0.95), (-L/2, -W/2 * 0.7),
            (-L/2 * 1.05, 0), (-L/2, W/2 * 0.7), (-L*0.3, W/2 * 0.95),
            (L*0.25, W/2),
        ]
        pts = []
        for x, y in hull_rel_pts:
            rx = px + x * math.cos(self.theta) - y * math.sin(self.theta)
            ry = py - (x * math.sin(self.theta) + y * math.cos(self.theta))
            pts.append([int(rx), int(ry)])
        boat_pts = np.array(pts, np.int32)
        cv2.fillConvexPoly(img, boat_pts, (245, 245, 245))
        cv2.polylines(img, [boat_pts], True, (20, 20, 20), 2)

        cockpit_rel_pts = [
            (L*0.1, W/2 * 0.65), (-L*0.3, W/2 * 0.65), (-L*0.42, W/2 * 0.4),
            (-L*0.42, -W/2 * 0.4), (-L*0.3, -W/2 * 0.65), (L*0.1, -W/2 * 0.65),
        ]
        c_pts = []
        for x, y in cockpit_rel_pts:
            rx = px + x * math.cos(self.theta) - y * math.sin(self.theta)
            ry = py - (x * math.sin(self.theta) + y * math.cos(self.theta))
            c_pts.append([int(rx), int(ry)])
        cockpit_pts = np.array(c_pts, np.int32)
        cv2.fillConvexPoly(img, cockpit_pts, (150, 150, 150))
        cv2.polylines(img, [cockpit_pts], True, (100, 100, 100), 1)

        mast_offset = L * 0.15
        mast_x = int(px + mast_offset * math.cos(self.theta))
        mast_y = int(py - mast_offset * math.sin(self.theta))
        cv2.circle(img, (mast_x, mast_y), 3, (40, 40, 40), 2)

        stern_x = int(px - math.cos(self.theta) * (L/2 * 1.05))
        stern_y = int(py + math.sin(self.theta) * (L/2 * 1.05))
        rudder_angle = self.theta + self.current_rudder
        rudder_end_x = int(stern_x - math.cos(rudder_angle) * (1.1 * self.scale))
        rudder_end_y = int(stern_y + math.sin(rudder_angle) * (1.1 * self.scale))
        cv2.line(img, (stern_x, stern_y), (rudder_end_x, rudder_end_y), (30, 30, 200), 3)

        actual_sail_rad = math.copysign(self.current_sail, self.wind_angle)
        sail_angle_global = self.theta + math.pi + actual_sail_rad
        sail_end_x = int(mast_x + math.cos(sail_angle_global) * (2.55 * self.scale))
        sail_end_y = int(mast_y - math.sin(sail_angle_global) * (2.55 * self.scale))
        cv2.line(img, (mast_x, mast_y), (sail_end_x, sail_end_y), (250, 250, 250), 4)

        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (250, 140), (0, 0, 0), -1)
        cv2.rectangle(overlay, (10, 150), (250, 280), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        
        cv2.putText(img, "TELEMETRY", (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "-" * 30, (20, 50), font, 0.5, (200, 200, 200), 1)
        cv2.putText(img, f"Speed: {self.speed:.2f} m/s", (20, 75), font, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"A-Wind: {self.wind_speed:.1f} m/s", (20, 100), font, 0.6, (255, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"Rudder: {math.degrees(self.current_rudder):.0f} deg", (20, 125), font, 0.6, (0, 100, 255), 1, cv2.LINE_AA)

        compass_cx, compass_cy = WIDTH - 80, 80
        cv2.circle(img, (compass_cx, compass_cy), 45, (30, 30, 30), -1)
        cv2.circle(img, (compass_cx, compass_cy), 45, (100, 100, 100), 2)
        cv2.putText(img, "N", (compass_cx - 5, compass_cy - 30), font, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
        for d in range(0, 360, 15):
            rad = math.radians(d)
            if d % 90 == 0:
                cv2.line(img, (int(compass_cx + math.cos(rad) * 45), int(compass_cy + math.sin(rad) * 45)),
                              (int(compass_cx + math.cos(rad) * 35), int(compass_cy + math.sin(rad) * 35)), (200, 200, 200), 2, cv2.LINE_AA)
            else:
                cv2.line(img, (int(compass_cx + math.cos(rad) * 45), int(compass_cy + math.sin(rad) * 45)),
                              (int(compass_cx + math.cos(rad) * 40), int(compass_cy + math.sin(rad) * 40)), (100, 100, 100), 1, cv2.LINE_AA)

        if hasattr(self, 'wind_sprite') and self.wind_sprite is not None:
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
                    img[y1:y2, x1:x2, c] = (alpha_s * rotated_wind[y1o:y2o, x1o:x2o, c] + alpha_l * img[y1:y2, x1:x2, c])

        def draw_slider(img, text, rect, val, max_val, disp_val, suffix=""):
            rx, ry, rw, rh = rect
            cv2.rectangle(img, (rx - 150, ry - 15), (rx + rw + 20, ry + rh + 15), (20, 20, 25), -1)
            cv2.rectangle(img, (rx - 150, ry - 15), (rx + rw + 20, ry + rh + 15), (80, 80, 80), 1)
            cv2.rectangle(img, (rx, ry + rh//2 - 2), (rx + rw, ry + rh//2 + 2), (60, 60, 60), -1)
            k_x = rx + int((val / max_val) * rw)
            cv2.rectangle(img, (rx, ry + rh//2 - 2), (k_x, ry + rh//2 + 2), (0, 200, 255), -1)
            cv2.circle(img, (k_x, ry + rh//2), 10, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(img, (k_x, ry + rh//2), 10, (100, 100, 100), 1, cv2.LINE_AA)
            label = f"{text}: {disp_val}{suffix}"
            cv2.putText(img, label, (rx - 130, ry + 12), font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        draw_slider(img, "Ruder (Soll)", (550, HEIGHT - 240, 350, 15), self.slider_rudder_val, 90, self.slider_rudder_val - 45, " Grad")
        draw_slider(img, "Segel (Soll)", (550, HEIGHT - 180, 350, 15), self.slider_sail_val, 70, self.slider_sail_val, " Grad")
        draw_slider(img, "T-Wind Speed", (550, HEIGHT - 120, 350, 15), self.slider_wspeed_val, 20, self.slider_wspeed_val, " m/s")
        draw_slider(img, "T-Wind Angle", (550, HEIGHT - 60,  350, 15), self.slider_wangle_val, 360, self.slider_wangle_val, " Grad")

        cv2.imshow(self.window_name, img)
        key = cv2.waitKey(1)
        if key == 27:
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = VisualizerNode()
    rclpy.spin(node)
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()