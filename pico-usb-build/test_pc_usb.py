#!/usr/bin/env python3
"""
PC-side USB test script for Pico 2
Komunikacja z Pico przez wirtualny port szeregowy (USB CDC)

Użycie:
    python3 test_pc_usb.py
    python3 test_pc_usb.py /dev/ttyACM0
"""

import serial
import sys
import time
from pathlib import Path

# Color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class PicoUSB:
    """High-level USB communication with Pico"""
    
    def __init__(self, port, baudrate=115200, timeout=1.0):
        """
        Initialize USB connection
        Args:
            port: Serial port (e.g., /dev/ttyACM0)
            baudrate: Baud rate (115200 for CDC)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.serial = None
        self.connected = False
        
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.connected = True
            print(f"{GREEN}✓{NC} Connected to {port} @ {baudrate} baud")
        except serial.SerialException as e:
            print(f"{RED}✗{NC} Failed to open {port}: {e}")
            raise
    
    def send(self, data):
        """Send data to Pico"""
        if not self.connected:
            raise RuntimeError("Not connected")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        self.serial.write(data)
        self.serial.flush()
    
    def receive(self, timeout=None):
        """Receive data from Pico"""
        if not self.connected:
            raise RuntimeError("Not connected")
        
        old_timeout = self.serial.timeout
        if timeout:
            self.serial.timeout = timeout
        
        try:
            data = self.serial.read(256)
        finally:
            self.serial.timeout = old_timeout
        
        return data
    
    def send_command(self, cmd):
        """Send a command and get response"""
        # Ensure \n at end
        if isinstance(cmd, str) and not cmd.endswith('\n'):
            cmd += '\n'
        
        print(f"{BLUE}→${NC} {cmd.strip()}")
        self.send(cmd)
        
        # Wait for response
        response = self.receive(timeout=1.0)
        if response:
            try:
                text = response.decode('utf-8').strip()
                print(f"{GREEN}←${NC} {text}")
                return text
            except UnicodeDecodeError:
                print(f"{YELLOW}←${NC} (binary data, {len(response)} bytes)")
                return response
        else:
            print(f"{YELLOW}←${NC} (timeout - no response)")
            return None
    
    def close(self):
        """Close connection"""
        if self.serial:
            self.serial.close()
            self.connected = False

def find_pico_port():
    """Auto-detect Pico serial port"""
    possible_ports = [
        '/dev/ttyACM0',
        '/dev/ttyACM1',
        '/dev/ttyUSB0',
        '/dev/ttyUSB1',
    ]
    
    for port in possible_ports:
        if Path(port).exists():
            print(f"{YELLOW}→${NC} Found potential Pico port: {port}")
            return port
    
    return None

def print_header():
    """Print welcome header"""
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║  Pico 2 USB Test - PC Side                             ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════╝{NC}\n")

def print_commands():
    """Print available commands"""
    print(f"\n{BLUE}Available Commands:{NC}")
    print("  PING       - Echo test")
    print("  STATUS     - Get device status")
    print("  INFO       - Get device info")
    print("  LED_ON     - Turn on built-in LED")
    print("  LED_OFF    - Turn off built-in LED")
    print("  RESET      - Reboot Pico")
    print("  HELP       - Get help from Pico")
    print()
    print("  send <msg> - Send raw message")
    print("  recv       - Receive data (raw)")
    print("  exit       - Quit this program")
    print()

def interactive_mode(pico):
    """Interactive command mode"""
    print_commands()
    
    while True:
        try:
            user_input = input(f"{YELLOW}> {NC}").strip()
        except KeyboardInterrupt:
            print("\n{RED}Interrupted{NC}")
            break
        except EOFError:
            break
        
        if not user_input:
            continue
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        elif user_input.lower() == 'recv':
            print("Waiting for data (5 seconds)...")
            data = pico.receive(timeout=5.0)
            if data:
                try:
                    print(f"{GREEN}←${NC} {data.decode('utf-8').strip()}")
                except:
                    print(f"{GREEN}←${NC} (binary): {data.hex()}")
        
        elif user_input.lower().startswith('send '):
            msg = user_input[5:]
            if msg.startswith('"') and msg.endswith('"'):
                msg = msg[1:-1]
            pico.send_command(msg)
        
        elif user_input.lower() == 'help':
            print_commands()
        
        else:
            # Treat as Pico command
            pico.send_command(user_input)

def test_mode(pico):
    """Automated test sequence"""
    print(f"{BLUE}Running automated tests...{NC}\n")
    
    tests = [
        ("PING", "Should respond PONG"),
        ("STATUS", "Device status"),
        ("INFO", "Device info"),
        ("LED_ON", "Turn LED on"),
        ("LED_OFF", "Turn LED off"),
        ("HELP", "Get command list"),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, desc in tests:
        print(f"\nTest: {desc}")
        try:
            response = pico.send_command(cmd)
            if response:
                passed += 1
            else:
                failed += 1
                print(f"{YELLOW}⚠${NC} No response")
        except Exception as e:
            failed += 1
            print(f"{RED}✗${NC} Error: {e}")
        
        time.sleep(0.2)
    
    print(f"\n{BLUE}─────────────────────────────────────────────────────{NC}")
    print(f"Tests passed: {GREEN}{passed}{NC}")
    print(f"Tests failed: {RED}{failed}{NC}")
    print(f"{BLUE}─────────────────────────────────────────────────────{NC}\n")
    
    return failed == 0

def main():
    print_header()
    
    # Find port
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = find_pico_port()
        if not port:
            print(f"{RED}✗${NC} Could not find Pico serial port")
            print("\nUsage:")
            print("  python3 test_pc_usb.py             # Auto-detect")
            print("  python3 test_pc_usb.py /dev/ttyACM0  # Specific port")
            print("\nFind available ports with:")
            print("  ls -la /dev/ttyACM*")
            sys.exit(1)
    
    # Connect
    try:
        pico = PicoUSB(port)
    except Exception as e:
        print(f"{RED}Connection failed: {e}{NC}")
        sys.exit(1)
    
    try:
        # Run automated tests first
        if test_mode(pico):
            print(f"{GREEN}✓${NC} Automated tests passed!\n")
        else:
            print(f"{YELLOW}⚠${NC} Some tests failed, but continuing...\n")
        
        # Enter interactive mode
        print(f"{BLUE}Entering interactive mode...{NC}")
        print(f"(Type 'help' for commands or 'exit' to quit)\n")
        interactive_mode(pico)
    
    except KeyboardInterrupt:
        print(f"\n{RED}Interrupted{NC}")
    
    finally:
        pico.close()
        print(f"{GREEN}✓${NC} Disconnected")

if __name__ == "__main__":
    main()
