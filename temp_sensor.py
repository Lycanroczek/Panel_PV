import machine
from machine import time, Pin, I2C

def temp_start():
    global temp
    temp = I2C(0, scl=Pin(7), sda=Pin(8),freq=100000)
    temp.scan()
    temp.writeto_mem(73,1,bytes([100,176])) #Configurating temperature sensor work after restart
    temp.writeto_mem(73,3,bytes([6,64])) #Configurating THIGH 100C
    temp.writeto_mem(73,2,bytes([5,160])) #Configurating TLOW 90C
    temp.writeto(73,bytes([0])) #Coming back to reading temperature

def reading_temp():
    read = temp.readfrom(73,2) #Requesting data from sensor
    value = read[0] 
    value = value << 8
    value = value + read[1]
    value = value >> 4
    value_2 = value & 2048
    if value_2 == 0: #Positive temperature
        value = value * 0.0625
        return value
    else: #Negative temperature
        value = value - 4096
        value = value * 0.0625
        return value
        
def alert_temp():
    alert = Pin(9, Pin.IN) #Reading alert pin from sensor
    alert = alert.value() 
    if alert == 1: 
        return 1 #Alert is active
    else:
        return 0 #Alert is not active
