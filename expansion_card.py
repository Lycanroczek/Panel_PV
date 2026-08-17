from machine import ADC
expansion = ADC(0)
def jest_podlcaczona():
    value = expansion.read_u16()
    voltage = value * 3.3 / (65535)
    if voltage <= 1.8:
        return 1
    else:
        return 0
