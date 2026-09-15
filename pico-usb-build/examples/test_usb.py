"""
Test script for USB CDC device
Run this on Pico to verify USB communication
"""

import sys
import time
from machine import Pin

# Import USB wrapper
sys.path.insert(0, '.')
from USB import USB, USBProtocol

# LED for status
led = Pin("LED", Pin.OUT)

def blink(times=1, duration=0.1):
    """Blink LED"""
    for _ in range(times):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)

def main():
    print("Raspberry Pi Pico 2 - USB CDC Test")
    print("=" * 50)
    
    # Initialize USB
    USB.init()
    print("USB initialized")
    blink(2)
    
    # Wait for USB connection
    print("Waiting for USB connection...")
    timeout = 50
    while not USB.is_connected() and timeout > 0:
        print(".", end="")
        time.sleep(0.1)
        timeout -= 1
    
    if not USB.is_connected():
        print("\nERROR: USB not connected!")
        blink(5)
        return
    
    print("\nUSB connected!")
    blink(3)
    
    # Wait for USB ready
    print("Waiting for USB device to be ready...")
    timeout = 50
    while not USB.is_ready() and timeout > 0:
        print(".", end="")
        time.sleep(0.1)
        timeout -= 1
    
    if not USB.is_ready():
        print("\nERROR: USB not ready!")
        blink(5)
        return
    
    print("\nUSB ready!")
    blink(3)
    
    # Send greeting
    USB.write_line("PICO_READY")
    print("Sent greeting: PICO_READY")
    
    # Simple command protocol
    print("\nEntering command loop (type commands on PC, end with newline)")
    print("Built-in commands:")
    print("  PING     -> PONG")
    print("  INFO     -> System info")
    print("  LED_ON   -> Turn on LED")
    print("  LED_OFF  -> Turn off LED")
    print("  RESET    -> Reboot Pico")
    print("-" * 50)
    
    cmd_buffer = ""
    
    while True:
        # Check for incoming data
        if USB.any() > 0:
            data = USB.read(256)
            if data:
                # Decode and process
                try:
                    chunk = data.decode('utf-8')
                    print(f"RX: {repr(chunk)}")
                    
                    cmd_buffer += chunk
                    
                    # Process complete lines
                    while '\n' in cmd_buffer:
                        cmd, cmd_buffer = cmd_buffer.split('\n', 1)
                        cmd = cmd.strip().upper()
                        
                        if cmd:
                            response = handle_command(cmd)
                            if response:
                                print(f"TX: {response}")
                                USB.write_line(response)
                
                except Exception as e:
                    print(f"ERROR: {e}")
                    USB.write_line(f"ERROR: {str(e)}")
        
        # Check USB status periodically
        if not USB.is_connected():
            print("USB disconnected!")
            break
        
        time.sleep(0.01)

def handle_command(cmd):
    """Handle incoming commands"""
    if cmd == "PING":
        return "PONG"
    
    elif cmd == "INFO":
        import os
        uname = os.uname()
        return f"Pico {uname.sysname}/{uname.machine}"
    
    elif cmd == "LED_ON":
        led.on()
        return "LED_ON"
    
    elif cmd == "LED_OFF":
        led.off()
        return "LED_OFF"
    
    elif cmd == "RESET":
        import machine
        USB.write_line("RESET_ACK")
        time.sleep(0.5)
        machine.reset()
        return None
    
    elif cmd == "ECHO":
        return "ECHO"
    
    else:
        return f"UNKNOWN: {cmd}"

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        USB.deinit()
    except Exception as e:
        print(f"ERROR: {e}")
        blink(10)
