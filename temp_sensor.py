import time
import machine
from machine import time, Pin, I2C

def temp_start():
    global temp
    temp = I2C(0, scl=Pin(7), sda=Pin(8),freq=100000)
    temp.scan()
    temp.writeto_mem(73,1,bytes([100,176])) #Configurating temperature sensor work after restart
    temp.writeto_mem(73,3,bytes([6,64])) #Configurating THIGH 100C
    temp.writeto_mem(73,2,bytes([5,160])) #Configuratin TLOW 90C
    temp.writeto(73,bytes([0])) #Coming back to reading temperature

def reading_temp():
    read = temp.readfrom(73,2)
    value = read[0] + read[1]
    value = value >> 4
    value = value * 0.0625
    return value


