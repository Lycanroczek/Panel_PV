from machine import Pin, I2C
def ADC_start():
    global ADC
    ADC = I2C(1, scl=Pin(19), sda=Pin(20), freq=100000)
    ADC.scan()
    ADC.writeto_mem(72,1,bytes([69,227])) #Loading configuration
    ADC.writeto(72,bytes([0])) #Changing from settings to measurements

def ADC_measurement_V():
    measurement_V = []
    ADC.writeto_mem(72,1,bytes([69,227]))
    ADC.writeto(72,bytes([0]))
    for i in range(8): #Reading 8 samples
        read = ADC.readfrom(72,2) 
        value = read[0] << 8 
        value = value + read[1]
        value = value*0.0000625
        measurement_V.append(value)
    return sum(measurement_V)/len(measurement_V) #Returning mean of those samples

def ADC_measurement_I():
    measurement_I = []
    ADC.writeto_mem(72,1,bytes([85,227]))
    ADC.writeto(72,bytes([0]))
    for i in range(8): #Reading 8 samples
        read = ADC.readfrom(72,2)
        value = read[0] << 8
        value = value + read[1]
        value = value*0.0000625
        measurement_I.append(value)
    return sum(measurement_I)/len(measurement_I) #Returning mean of those samples