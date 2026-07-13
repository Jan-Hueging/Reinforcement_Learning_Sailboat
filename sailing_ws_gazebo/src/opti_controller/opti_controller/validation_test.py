#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
import pandas as pd
import matplotlib.pyplot as plt
import math

class SailSimTimeAutomation(Node):
    def __init__(self):
        super().__init__('sail_sim_time_automation')
        
        # --- PUBLISHER ---
        self.rudder_pub = self.create_publisher(Float64, '/Ruderstellung_Soll', 10)
        self.sail_pub = self.create_publisher(Float64, '/Segelstellung_Soll', 10)
        
        # --- SUBSCRIBER ---
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.roll_sub = self.create_subscription(Float64, '/Neigung', self.roll_callback, 10)
        self.heading_sub = self.create_subscription(Float64, '/Kompass', self.heading_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/model/opti_boot/odometry', self.odom_callback, 10)
        
        # --- TIMER ---
        self.timer = self.create_timer(0.1, self.test_loop)
        
        # --- SENSOR-DATEN ---
        self.sim_time = None
        self.sim_start_time = None
        self.last_sim_time = None
        
        self.current_roll = 0.0
        self.current_heading = 0.0
        self.current_speed = 0.0  # Mathematisch integrierte Vorwärtsgeschwindigkeit

        self.last_x = None
        self.last_y = None
        self.last_pose_time = None
        
        # --- TESTSTEUERUNG ---
        self.data_log = []
        self.cmd_rudder = 0.0
        self.cmd_sail = 0.5
        self.test_finished = False

        self.get_logger().info('Synchronisiertes Testskript mit Geschwindigkeitsmessung gestartet...')

    def imu_callback(self, msg):
        self.sim_time = msg.header.stamp.sec + (msg.header.stamp.nanosec * 1e-9)

    def odom_callback(self, msg):
        # Simulationszeit aus dem Header holen
        self.sim_time = msg.header.stamp.sec + (msg.header.stamp.nanosec * 1e-9)
        
        # Exakte lineare Vorwärts- und Quergeschwindigkeit auslesen
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        
        # Absolute Geschwindigkeit über Grund berechnen
        self.current_speed = math.sqrt(vx**2 + vy**2)

    def roll_callback(self, msg):
        self.current_roll = msg.data

    def heading_callback(self, msg):
        self.current_heading = msg.data

    def test_loop(self):
        if self.sim_time is None or self.test_finished:
            return
            
        if self.sim_start_time is None:
            self.sim_start_time = self.sim_time
            self.get_logger().info(f'Simulation gestartet! Test-Synchronisation bei Sim-Sekunde: {self.sim_start_time:.2f}')
            return
            
        # Berechne die verstrichene Simulationszeit seit dem Klick auf Play
        elapsed_sim_time = self.sim_time - self.sim_start_time

        # --- REINE INTERVALLSTEUERUNG AB PLAY-KLICK ---
        
        if elapsed_sim_time < 5.0:
            self.cmd_rudder = 0.0
            self.cmd_sail = 0.5  
            
        elif elapsed_sim_time >= 5.0 and elapsed_sim_time < 25.0:
            self.cmd_rudder = 0.0
            self.cmd_sail = 0.5  
            
        elif elapsed_sim_time >= 25.0 and elapsed_sim_time < 30.0:
            self.cmd_rudder = -0.4 # -0.4 für Wende
            self.cmd_sail = 0.3 # 0.3 für Wende   
            
        elif elapsed_sim_time >= 30.0 and elapsed_sim_time < 50.0:
            self.cmd_rudder = 0.0  
            self.cmd_sail = 0.5    
            
        else:
            self.test_finished = True
            self.timer.cancel()
            self.save_and_plot_results()
            return
        
        """
        if elapsed_sim_time < 10.0:
            self.cmd_rudder = 0.0
            self.cmd_sail = 0.5  
            
        elif elapsed_sim_time >= 10.0 and elapsed_sim_time < 12.0:
            self.cmd_rudder = -0.3
            self.cmd_sail = 0.5  
            
        elif elapsed_sim_time >= 12.0 and elapsed_sim_time < 30.0:
            self.cmd_rudder = 0.0 # -0.4 für Wende
            self.cmd_sail = 0.5 # 0.3 für Wende   
            
        elif elapsed_sim_time >= 30.0 and elapsed_sim_time < 50.0:
            self.cmd_rudder = 0.0  
            self.cmd_sail = 0.5    
            
        else:
            self.test_finished = True
            self.timer.cancel()
            self.save_and_plot_results()
            return
        """

        # Sende Befehle
        r_msg = Float64()
        r_msg.data = self.cmd_rudder
        self.rudder_pub.publish(r_msg)
        
        s_msg = Float64()
        s_msg.data = self.cmd_sail
        self.sail_pub.publish(s_msg)

        # Logge Daten
        self.data_log.append({
            'time': elapsed_sim_time,
            'speed': self.current_speed,
            'sail_limit': self.cmd_sail,
            'roll': self.current_roll,
            'heading': self.current_heading,
            'rudder': self.cmd_rudder
        })


    def save_and_plot_results(self):
        self.get_logger().info('Testzeit abgelaufen. Generiere 4-Zonen-Diagramm...')
        df = pd.DataFrame(self.data_log)
        df.to_csv('sim_data_zeit_wendemanoever.csv', index=False)
        
        # Erstelle 4 Diagramme untereinander (inklusive Geschwindigkeit!)
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, sharex=True, figsize=(8, 12))
        
        # Plot 1: Geschwindigkeit über Grund
        ax1.plot(df['time'], df['speed'], color='blue', linewidth=2, label='Geschwindigkeit (integriert)')
        ax1.set_ylabel('Geschwindigkeit [m/s]', fontsize=10)
        ax1.grid(True, linestyle='--')
        ax1.set_title('Simulationszeit-synchronisierte Validierung: Wende', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right')
        
        # Plot 2: Kurs (Kompass)
        ax2.plot(df['time'], df['heading'], color='purple', linewidth=2, label='Boot-Kurs (Kompass)')
        ax2.set_ylabel('Kurs [rad]', fontsize=10)
        ax2.grid(True, linestyle='--')
        ax2.legend(loc='upper right')
        
        # Plot 3: Schot & Ruder
        ax3.plot(df['time'], df['sail_limit'], color='green', linewidth=2, label='Schot-Limit (Soll)')
        ax3.plot(df['time'], df['rudder'], color='orange', linewidth=1.5, linestyle=':', label='Ruder-Soll')
        ax3.set_ylabel('Steuerwinkel [rad]', fontsize=10)
        ax3.grid(True, linestyle='--')
        ax3.legend(loc='upper right')
        
        # Plot 4: Krängung (Neigung)
        ax4.plot(df['time'], df['roll'], color='red', linewidth=2, label='Krängung (Neigung)')
        ax4.set_ylabel('Krängungswinkel [rad]', fontsize=10)
        ax4.set_xlabel('Simulationszeit (unabhängig von RTF) [s]', fontsize=11)
        ax4.grid(True, linestyle='--')
        ax4.legend(loc='upper right')
        
        plt.tight_layout()
        plt.savefig('validierung_simzeit_wende.pdf', format='pdf', dpi=300)
        plt.savefig('validierung_simzeit_wende.png', format='png', dpi=150)
        self.get_logger().info('PDF und PNG inklusive Geschwindigkeit erfolgreich exportiert!')

def main(args=None):
    rclpy.init(args=args)
    node = SailSimTimeAutomation()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
