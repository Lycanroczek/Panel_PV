import machine
from machine import Pin
import time

class SoftUART:
    def __init__(self, tx_pin, rx_pin, baudrate=115200):
        self.tx = Pin(tx_pin, Pin.OUT)
        self.rx = Pin(rx_pin, Pin.IN)
        self.bit_delay = 1.0 / baudrate
        self.tx.value(1)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        for byte in data:
            self.tx.value(0)
            time.sleep(self.bit_delay)
            for i in range(8):
                self.tx.value((byte >> i) & 1)
                time.sleep(self.bit_delay)
            self.tx.value(1)
            time.sleep(self.bit_delay * 2)

    def any(self):
        return 0

    def read(self, n=1):
        return b''

uart = SoftUART(tx_pin=4, rx_pin=6, baudrate=115200)
DE_RE = Pin(5, Pin.OUT)
rx_buffer = b''

def reading():
    global rx_buffer
    DE_RE.value(0)
    return None

def sending(data):
    DE_RE.value(1)
    uart.write(data + b'\n')
    time.sleep_us(500)
    DE_RE.value(0)