"""
Main application for Pico 2 with RS485 and USB CDC
Integrates RS485 module and USB service
"""

import sys
import time
from machine import Pin

# Import modules
from RS485 import reading, sending
from USB import USB, USBProtocol

# Built-in LED
led = Pin("LED", Pin.OUT)

def blink_pattern(pattern, duration=0.1):
    """Blink LED with pattern (1=on, 0=off)"""
    for bit in pattern:
        if bit:
            led.on()
        else:
            led.off()
        time.sleep(duration)
    led.off()

def main():
    print("\n" + "="*60)
    print("Pico 2 Multi-Protocol Application")
    print("RS485 + USB CDC Service")
    print("="*60)
    
    # Initialize USB (GPIO 10/11)
    try:
        USB.init()
        print("[USB] Initializing...")
        blink_pattern([1, 0, 1, 0, 1])
    except Exception as e:
        print(f"[USB] ERROR: {e}")
    
    # Initialize RS485 (UART0, GPIO0/1 + DE on GPIO5)
    try:
        rs485 = True
        print("[RS485] Initialized")
        blink_pattern([1, 1, 0, 1, 1])
    except Exception as e:
        print(f"[RS485] ERROR: {e}")
        rs485 = None
    
    # Wait for USB connection
    print("\n[MAIN] Waiting for USB connection...")
    timeout = 100
    while not USB.is_connected() and timeout > 0:
        print(".", end="", flush=True)
        time.sleep(0.1)
        timeout -= 1
    
    if USB.is_connected():
        print("\n[MAIN] USB connected!")
        blink_pattern([1]*5)
    else:
        print("\n[MAIN] USB not connected (continuing offline)")
    
    # Setup command handler
    def handle_usb_command(cmd):
        """Handle commands from USB"""
        cmd = cmd.strip().upper()
        
        if cmd == "PING":
            return "PONG"
        
        elif cmd == "STATUS":
            usb_status = "READY" if USB.is_ready() else "CONNECTED" if USB.is_connected() else "DISCONNECTED"
            rs485_status = "OK" if rs485 else "OFFLINE"
            return f"USB:{usb_status} RS485:{rs485_status}"
        
        elif cmd == "LED_ON":
            led.on()
            return "LED:ON"
        
        elif cmd == "LED_OFF":
            led.off()
            return "LED:OFF"
        
        elif cmd.startswith("RS485:"):
            # Send command to RS485
            if rs485:
                msg = cmd[6:].encode()
                sending(msg)
                return "RS485:SENT"
            return "RS485:OFFLINE"
        
        elif cmd == "HELP":
            return "Commands: PING, STATUS, LED_ON, LED_OFF, RS485:msg, HELP"
        
        else:
            return f"UNKNOWN: {cmd}"
    
    protocol = USBProtocol(on_command=handle_usb_command)
    
    # Main loop
    print("\n[MAIN] Starting main loop...")
    print("-" * 60)
    
    usb_error_count = 0
    rs485_error_count = 0
    
    try:
        while True:
            # Check USB
            try:
                if USB.is_connected():
                    protocol.process()  # Process incoming USB commands
                    
                    # Check USB for data (polling)
                    if USB.any() > 0:
                        usb_error_count = 0
                else:
                    # USB disconnected - reset buffer
                    protocol.cmd_buffer = ""
                    
            except Exception as e:
                usb_error_count += 1
                if usb_error_count > 100:
                    print(f"[USB] ERROR: {e}")
                    usb_error_count = 0
            
            # Check RS485
            try:
                if rs485:
                    # Check if there's data from RS485
                    data = reading()
                    if data:
                        # Forward to USB if connected
                        if USB.is_connected():
                            USB.write(b"RS485:")
                            USB.write(data)
                            USB.write(b"\n")
                            print(f"[RS485->USB] {data}")
            
            except Exception as e:
                rs485_error_count += 1
                if rs485_error_count > 100:
                    print(f"[RS485] ERROR: {e}")
                    rs485_error_count = 0
            
            # Heartbeat
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")
    
    finally:
        USB.deinit()

if __name__ == "__main__":
    main()
