from tkinter import *
from tkinter import ttk

root = Tk()
root.title("PV Characteristics")
main_screen = ttk.Frame(root, padding=(2,4,12,12))
main_screen.pack()
voltage_entry = ttk.Entry(main_screen)
voltage_entry.pack()
voltage_label = ttk.Label(main_screen,text="Voltage")
voltage_label.pack()
current_entry = ttk.Entry(main_screen)
current_label = ttk.Label(main_screen,text="Current")
current_entry.pack()
current_label.pack()
root.mainloop()