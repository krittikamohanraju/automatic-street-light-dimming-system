"""
Real-Time Street Light Monitoring System
Reads data from Arduino/ESP32 and displays live statistics
Saves data to CSV for analysis
"""

try:
    import serial
except ImportError:
    serial = None
import time
import argparse
import csv
from datetime import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

class StreetLightMonitor:
    def __init__(self, port='COM3', baudrate=115200, simulate=False, max_simulate=10):
        """
        Initialize the street light monitor
        
        Args:
            port: Serial port (COM3, COM4 for Windows; /dev/ttyUSB0 for Linux)
            baudrate: Communication speed (default 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.data_file = f"streetlight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Data storage for real-time plotting
        self.max_points = 100
        self.timestamps = deque(maxlen=self.max_points)
        self.ambient_light = deque(maxlen=self.max_points)
        self.brightness_levels = deque(maxlen=self.max_points)
        self.motion_status = deque(maxlen=self.max_points)
        # Simulation mode
        self.simulate = simulate
        self.max_simulate = max_simulate
        self._simulate_count = 0
        
    def connect(self):
        """Establish serial connection with the device"""
        try:
            # If simulate, skip opening a real serial port
            if self.simulate:
                print("Simulation mode enabled — no serial port will be opened")
                return True

            if serial is None:
                print("Error: pyserial not available. Use --simulate to run without hardware.")
                return False

            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for connection to stabilize
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"Error connecting to {self.port}: {e}")
            if serial:
                print("\nAvailable ports:")
                self.list_ports()
            return False
    
    @staticmethod
    def list_ports():
        """List available serial ports"""
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"  - {port.device}: {port.description}")
    
    def initialize_csv(self):
        """Create CSV file with headers"""
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'System_Time_ms', 'Ambient_Light', 
                           'Brightness', 'Motion_Detected', 'Active_Mode'])
        print(f"Data logging to: {self.data_file}")
    
    def read_data(self):
        """Read and parse data from serial port"""
        try:
            # Simulation path
            if self.simulate:
                return self._simulate_read_data()

            if self.serial_connection and self.serial_connection.in_waiting > 0:
                line = self.serial_connection.readline().decode('utf-8').strip()

                # Skip non-data lines
                if not line or '=' in line or '-' in line:
                    return None

                # Parse CSV format: time,light,brightness,motion,active
                parts = line.split(',')
                if len(parts) == 5:
                    data = {
                        'system_time': int(parts[0]),
                        'ambient_light': int(parts[1]),
                        'brightness': int(parts[2]),
                        'motion': int(parts[3]),
                        'active_mode': int(parts[4]),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return data
        except Exception as e:
            print(f"Error reading data: {e}")
        return None

    def _simulate_read_data(self):
        """Generate simulated sensor data for testing"""
        if self._simulate_count >= self.max_simulate:
            return None

        t = int(time.time() * 1000) % 100000
        # simple oscillations for ambient light and brightness
        ambient = int(1500 + 1200 * (0.5 + 0.5 * __import__('math').sin(self._simulate_count / 2)))
        motion = 1 if (self._simulate_count % 5 == 0) else 0
        brightness = 255 if ambient < 800 or motion else int(100 + 100 * (ambient / 3000))
        active = 1 if brightness > 200 else 0

        data = {
            'system_time': t,
            'ambient_light': ambient,
            'brightness': brightness,
            'motion': motion,
            'active_mode': active,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self._simulate_count += 1
        return data
    
    def save_data(self, data):
        """Append data to CSV file"""
        with open(self.data_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['timestamp'],
                data['system_time'],
                data['ambient_light'],
                data['brightness'],
                data['motion'],
                data['active_mode']
            ])
    
    def display_stats(self, data):
        """Display real-time statistics"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("╔════════════════════════════════════════════════════════╗")
        print("║   REAL-TIME STREET LIGHT MONITORING SYSTEM             ║")
        print("╚════════════════════════════════════════════════════════╝")
        print(f"\nTime: {data['timestamp']}")
        print(f"Ambient Light Level: {data['ambient_light']}")
        print(f"Current Brightness: {data['brightness']}/255 ({data['brightness']*100//255}%)")
        print(f"Motion Detected: {'YES' if data['motion'] else 'NO'}")
        print(f"Active Mode: {'HIGH BRIGHTNESS' if data['active_mode'] else 'NORMAL'}")
        
        # Calculate energy saving
        energy_saved = 100 - (data['brightness'] * 100 // 255)
        print(f"Energy Saving: {energy_saved}%")
        
        # Status indicator
        if data['ambient_light'] > 2000:
            status = "DAYTIME - Lights OFF"
        elif data['ambient_light'] > 1000:
            status = "TWILIGHT - Dimmed"
        else:
            status = "NIGHT - Active"
        print(f"\nStatus: {status}")
        
        print("\n" + "-" * 58)
        print(f"Logging to: {self.data_file}")
        print("Press Ctrl+C to stop monitoring")
    
    def run(self):
        """Main monitoring loop"""
        if not self.connect():
            return
        
        self.initialize_csv()
        print("\n🔄 Starting real-time monitoring...\n")
        time.sleep(1)
        
        try:
            while True:
                data = self.read_data()
                if data:
                    self.save_data(data)
                    self.display_stats(data)

                    # Store for plotting
                    self.timestamps.append(time.time())
                    self.ambient_light.append(data['ambient_light'])
                    self.brightness_levels.append(data['brightness'])
                    self.motion_status.append(data['motion'])

                # In simulation mode exit after generating the requested number
                if self.simulate and self._simulate_count >= self.max_simulate:
                    print('\n✓ Simulation complete')
                    break

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n✓ Monitoring stopped by user")
        finally:
            if self.serial_connection:
                self.serial_connection.close()
                print("✓ Serial connection closed")
    
    def plot_realtime(self):
        """Create real-time plotting visualization"""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        
        def animate(frame):
            if len(self.timestamps) > 0:
                times = list(self.timestamps)
                
                # Plot ambient light
                ax1.clear()
                ax1.plot(times, list(self.ambient_light), 'b-', label='Ambient Light')
                ax1.set_ylabel('Light Level')
                ax1.set_title('Real-Time Street Light Monitoring')
                ax1.legend()
                ax1.grid(True)
                
                # Plot brightness
                ax2.clear()
                ax2.plot(times, list(self.brightness_levels), 'g-', label='LED Brightness')
                ax2.set_ylabel('Brightness (0-255)')
                ax2.legend()
                ax2.grid(True)
                
                # Plot motion
                ax3.clear()
                ax3.plot(times, list(self.motion_status), 'r-', label='Motion Detected')
                ax3.set_ylabel('Motion (0/1)')
                ax3.set_xlabel('Time')
                ax3.legend()
                ax3.grid(True)
        
        ani = FuncAnimation(fig, animate, interval=1000)
        plt.tight_layout()
        plt.show()


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("  AUTOMATIC STREET LIGHT DIMMING - REAL-TIME MONITOR")
    print("="*60 + "\n")
    parser = argparse.ArgumentParser(description='Street Light Monitor')
    parser.add_argument('--port', default='COM3', help='Serial port (COMx or /dev/tty)')
    parser.add_argument('--baud', default=115200, type=int, help='Baud rate')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode')
    parser.add_argument('--sim-iterations', default=10, type=int, help='Simulated samples to generate')
    args = parser.parse_args()

    # Create monitor instance
    monitor = StreetLightMonitor(port=args.port, baudrate=args.baud, simulate=args.simulate, max_simulate=args.sim_iterations)

    # Run monitoring
    monitor.run()


if __name__ == "__main__":
    main()
