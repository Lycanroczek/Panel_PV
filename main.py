import machine
import sys
import select
from ADC import ADC_start, ADC_measurement_I, ADC_measurement_V, ADC_test
from expansion_card import is_connected
from MCP import DAC_set, DAC_start
from RS485 import reading, sending
from temp_sensor import temp_start, reading_temp, alert_temp
from time import sleep_us, sleep

DAC_START = 1
DAC_END = 2681
offset = 0

SETTLING_DELAY_US = 6

temp_start()
DAC_start()
try:
    ADC_start()
except Exception:
    pass

connected = is_connected()
if connected == 1:
    DAC_END = DAC_END
else:
    DAC_END = DAC_END/2

def check_stdin():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip()
    return None

while True:
    cmd = check_stdin()

    if cmd == "ADC_TEST":
        try:
            val = ADC_test()
            print(f"ADC_TEST,{val}")
        except Exception as e:
            print(f"ERROR,ADC: {e}")

    elif cmd == "START":
        for dac_value in range(DAC_START, DAC_END + 1):
            sub_cmd = check_stdin()
            if sub_cmd == "STOP":
                DAC_set(0)
                break
            
            DAC_set(dac_value)
            sleep_us(SETTLING_DELAY_US)

            try:
                voltage = ADC_measurement_V() + offset
                current = ADC_measurement_I() + offset
            except Exception:
                voltage, current = 0.0, 0.0

            temperature = reading_temp()

            data = f"{voltage},{current}"
            temp_data = f"TEMP,{temperature}"
            
            print(data)
            print(temp_data)

            sending(data.encode())
            sending(temp_data.encode())

        print("FINISHED")
        sending(b"FINISHED")

    else:
        # Stan spoczynku - działa od razu po odpaleniu Pico, bez czekania na START
        try:
            temperature = reading_temp()
            temp_data = f"TEMP,{temperature}"
            print(temp_data)
            sending(temp_data.encode())
        except Exception:
            pass

        sleep(1)