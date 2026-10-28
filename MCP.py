from machine import Pin, SoftI2C

def DAC_start():
    global DAC
    DAC = SoftI2C(scl=Pin(16), sda=Pin(17), freq=100000)
    DAC.scan()

def DAC_set(value):
    data_high = value >> 4
    data_low = (value & 0x0F) << 4
    DAC.writeto(96, bytes([data_high, data_low]))