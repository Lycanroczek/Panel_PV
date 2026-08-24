from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import serial.tools.list_ports
from tkinter import filedialog

def connect():
    selected_port = port_list.get()

    try:
        connection = serial.Serial(selected_port, 115200, timeout=1)
    except:
        messagebox.showerror("","Not Connected")
        return
    messagebox.showinfo("", "Connected")
    open_main_menu(selected_port, connection)

def console_write(console, message):
    console.config(state="normal")
    console.insert("end", message + "\n")
    console.see("end")
    console.config(state="disabled")

def open_main_menu(selected_port, connection):
    root.geometry("1080x720+100+100")
    port_screen.destroy()

    main_screen = ttk.Frame(root, padding=20)
    main_screen.pack(fill="both", expand=True)

    top_bar = ttk.Frame(main_screen)
    top_bar.pack(fill="x")

    status_frame = ttk.Frame(top_bar)
    status_frame.pack()

    status_dot = ttk.Label(status_frame,text="●",foreground="green",font=("TkDefaultFont", 14))
    status_dot.pack(side="left")

    status_label = ttk.Label(status_frame,text=f"Connected  {selected_port}")
    status_label.pack(side="left", padx=(0, 0))

    separator = ttk.Separator(main_screen,orient="horizontal")
    separator.pack(fill="x", pady=10)

    send_files_button = ttk.Button(main_screen,text="SEND FILED TO PICO", command=select_files)
    send_files_button.pack(pady=(5,30))
    measurements_frame = ttk.Frame(main_screen)
    measurements_frame.pack()

    voltage_frame = ttk.LabelFrame(measurements_frame,text="Voltage",padding=20)
    voltage_frame.grid(row=0, column=0, padx=10)

    voltage_value = ttk.Label(voltage_frame,text="0.00 V",font=("TkDefaultFont", 16))
    voltage_value.pack()

    current_frame = ttk.LabelFrame(measurements_frame,text="Current",padding=20)
    current_frame.grid(row=0, column=1, padx=10)

    current_value = ttk.Label(current_frame,text="0.00 A",font=("TkDefaultFont", 16))
    current_value.pack()

    temperature_frame = ttk.LabelFrame(measurements_frame,text="Temperature",padding=20)
    temperature_frame.grid(row=0, column=2, padx=10)

    temperature_value = ttk.Label(temperature_frame,text="0.00 °C",font=("TkDefaultFont", 16))
    temperature_value.pack()

    start_button = ttk.Button(main_screen,text="START CHARACTERISTIC", command=start_characteristic)
    start_button.pack(pady=(20, 30))

    console_frame = ttk.LabelFrame(main_screen,text="Console",padding=10)
    console_frame.pack(fill="both",expand=True)

    console = Text(console_frame,height=10,state="disabled")
    console.pack(fill="both", expand=True)

    console_write(console, "Connected")
    console_write(console, f"Port: {selected_port}")
    
    check_connection(selected_port, status_dot, status_label)

def select_files():
    files = filedialog.askopenfilenames(title="Select files to send to Pico",filetypes=[("Python files", "*.py"),("All files", "*.*")])

    if files:
        print("Selected files:")
        for file in files:
            print(file)

def start_characteristic():
    characteristic_window = Toplevel(root)
    characteristic_window.title("I/V Characteristic")
    characteristic_window.geometry("1080x720")

    graph_frame = ttk.Frame(characteristic_window,padding=10)
    graph_frame.pack(fill="both",expand=True)

    status_label = ttk.Label(characteristic_window,text="Measuring...")
    status_label.pack(pady=10)

    status_label.config(text="Characteristic finished")

def check_connection(selected_port, status_dot, status_label):
    ports = serial.tools.list_ports.comports()

    connected = any(
        p.device == selected_port
        for p in ports
    )

    if connected:
        status_dot.config(foreground="green")
        status_label.config(text=f"Connected  {selected_port}")
    else:
        status_dot.config(foreground="red")
        status_label.config(text="Disconnected")

    root.after(1000, check_connection, selected_port, status_dot, status_label)

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