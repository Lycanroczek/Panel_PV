import machine
from machine import Pin, UART

uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(4), rx=Pin(6))
DE_RE = Pin(5, Pin.OUT)
rx_buffer = b''
def reading():
    global rx_buffer
    DE_RE.value(0)

    if uart.any():
        rx_buffer = uart.read()

        if b'\n' in rx_buffer:
            data, rx_buffer = rx_buffer.split(b'\n',1)
            return data

def sending(data):
    DE_RE.value(1)

    uart.write(data + b'\n')

    while not uart.txdone():
        pass

    DE_RE.value(0)
