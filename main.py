import machine
from machine import UART, Pin
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import serial.tools.list_ports
from tkinter import filedialog
from menu import connect, console_write, open_main_menu, select_files, start_characteristic, check_connection
from expansion_card import is_connected
from temp_sensor import temp_start, reading_temp, alert_temp
from ADC import ADC_start, ADC_measurement_I, ADC_measurement_V

global uart
uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(4), rx=Pin(6))

port = serial.tools.list_ports.comports()

root = Tk()
root.title("PV Characteristics")

port_screen = ttk.Frame(root,padding=20)
port_screen.pack()

port_screen_label = ttk.Label(port_screen,text="Choose port")
port_screen_label.pack()

port_list = ttk.Combobox(port_screen, state="readonly")
port_list.pack()

port_list["values"] = [p.device for p in port if p.vid is not None]
port_list.select_clear()
port_list.set("Choose port...")

connect_button = ttk.Button(port_screen,text="Connect",command=connect)
connect_button.pack()

root.mainloop()