"""
USB Service Module for Raspberry Pi Pico 2
Wraps usb_device C module with higher-level interface
"""

import usb_device as _usb_device

class USB:
    """Simple USB CDC device interface"""
    
    _initialized = False
    
    @staticmethod
    def init():
        """Initialize USB CDC device on GPIO 10/11"""
        _usb_device.init()
        USB._initialized = True
        print("[USB] Initialized on GPIO10 (D+) / GPIO11 (D-)")
    
    @staticmethod
    def is_ready():
        """Check if USB is connected and ready"""
        return _usb_device.is_ready()
    
    @staticmethod
    def is_connected():
        """Check if USB is connected (but not necessarily ready)"""
        return _usb_device.is_connected()
    
    @staticmethod
    def any():
        """Return number of bytes available to read"""
        return _usb_device.any()
    
    @staticmethod
    def read(n=None):
        """
        Read bytes from USB
        Args:
            n: number of bytes to read (default: all available)
        Returns:
            bytes object
        """
        if n is None:
            return _usb_device.read(256)
        return _usb_device.read(n)
    
    @staticmethod
    def read_line():
        """Read until newline character"""
        return _usb_device.read_line()
    
    @staticmethod
    def read_string():
        """Read bytes and decode as string"""
        data = _usb_device.read(256)
        if data:
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return None
        return ""
    
    @staticmethod
    def write(data):
        """
        Write bytes to USB
        Args:
            data: bytes or bytearray
        Returns:
            number of bytes written
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return _usb_device.write(data)
    
    @staticmethod
    def write_line(msg):
        """Write string with newline"""
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8')
        return USB.write(msg + '\n')
    
    @staticmethod
    def flush():
        """Flush USB output buffer"""
        _usb_device.flush()
    
    @staticmethod
    def deinit():
        """Deinitialize USB"""
        _usb_device.deinit()
        USB._initialized = False


# High-level protocol handler for communication with PC
class USBProtocol:
    """Simple line-based protocol handler (commands terminated with \\n)"""
    
    def __init__(self, on_command=None, timeout_ms=5000):
        """
        Initialize protocol handler
        Args:
            on_command: callback(command_str) -> response_str
            timeout_ms: command timeout
        """
        self.on_command = on_command
        self.timeout_ms = timeout_ms
        self.cmd_buffer = ""
    
    def process(self):
        """Process incoming USB data - call from main loop"""
        while USB.any() > 0:
            data = USB.read(256)
            if data:
                try:
                    chunk = data.decode('utf-8')
                    self.cmd_buffer += chunk
                    
                    # Process complete commands (ending with \n)
                    while '\n' in self.cmd_buffer:
                        cmd, self.cmd_buffer = self.cmd_buffer.split('\n', 1)
                        cmd = cmd.strip()
                        
                        if cmd:
                            self.handle_command(cmd)
                
                except UnicodeDecodeError:
                    self.cmd_buffer = ""
    
    def handle_command(self, cmd):
        """Handle a single command"""
        if self.on_command:
            try:
                response = self.on_command(cmd)
                if response:
                    USB.write(response)
                    if not response.endswith('\n'):
                        USB.write(b'\n')
            except Exception as e:
                USB.write(b"ERROR: " + str(e).encode() + b"\n")
        else:
            # Echo by default
            USB.write(b"OK\n")
