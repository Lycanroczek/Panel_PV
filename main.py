import machine
from ADC import ADC_start, ADC_measurement_I, ADC_measurement_V
from expansion_card import is_connected
from MCP import DAC_set, DAC_start
from RS485 import reading, sending
from temp_sensor import temp_start, reading_temp, alert_temp
from time import sleep_us, sleep

DAC_START = 1
DAC_END = 2681

SETTLING_DELAY_US = 6

temp_start()

DAC_start()

connected = is_connected()

if connected == 1:
    number_mosfet = 4
else:
    number_mosfet = 2

ADC_start()

while True:

    command = input()

    if command == "START":

        for dac_value in range(DAC_START, DAC_END + 1):

            # Setting DAC value
            DAC_set(dac_value)

            # Waiting for transistors
            sleep_us(SETTLING_DELAY_US)

            # getting mean of voltage
            voltage = ADC_measurement_V()

            # getting mean of current
            current = ADC_measurement_I()

            temperature = reading_temp()

            data = str(voltage) + "," + str(current)

            temp_data = "TEMP," + str(temperature)
            # Sending data to PC via USB
            print(data)
            print(temp_data)

            # Sending data via RS485
            sending(data.encode())
            sending(temp_data.encode())

        print("FINISHED")
        sending(b"FINISHED")

        while True:
            temperature = reading_temp()

            temp_data = "TEMP," + str(temperature)

            print(temp_data)

            sending(temp_data.encode())

            sleep(1) 