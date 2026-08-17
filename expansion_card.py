#from machine import ADC
#expansion = ADC(0)
value = 65535
def jest_podlcaczona():
    #value = expansion.read_u16()
    napiecie = value * 3.3 / (65535)
    print(napiecie)
    if napiecie <= 1.8:
        return 1
    else:
        return 0
