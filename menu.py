from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import serial
import serial.tools.list_ports
import subprocess
import os
import csv
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def connect():
    selected_port = port_list.get()

    if not selected_port:
        messagebox.showerror("","Select Pico port")
        return

    try:
        connection = serial.Serial(selected_port,115200,timeout=1)
    except Exception as e:
        messagebox.showerror("",f"Not Connected\n\n{e}")
        return

    messagebox.showinfo("","Connected")
    open_main_menu(selected_port,connection)


def console_write(console,message):
    console.config(state="normal")
    console.insert("end",message + "\n")
    console.see("end")
    console.config(state="disabled")


def open_main_menu(selected_port,connection):
    root.geometry("1080x720+100+100")
    port_screen.destroy()

    main_screen = ttk.Frame(root,padding=20)
    main_screen.pack(fill="both",expand=True)

    # TOP BAR

    top_bar = ttk.Frame(main_screen)
    top_bar.pack(fill="x")

    status_frame = ttk.Frame(top_bar)
    status_frame.pack()

    status_dot = ttk.Label(status_frame,text="●",foreground="green",font=("TkDefaultFont",14))
    status_dot.pack(side="left")

    status_label = ttk.Label(status_frame,text=f"Connected  {selected_port}")
    status_label.pack(side="left")

    separator = ttk.Separator(main_screen,orient="horizontal")
    separator.pack(fill="x",pady=10)

    # MEASUREMENTS

    measurements_frame = ttk.Frame(main_screen)
    measurements_frame.pack()

    voltage_frame = ttk.LabelFrame(measurements_frame,text="Voltage",padding=20)
    voltage_frame.grid(row=0,column=0,padx=10)

    voltage_value = ttk.Label(voltage_frame,text="0.00 V",font=("TkDefaultFont",16))
    voltage_value.pack()

    current_frame = ttk.LabelFrame(measurements_frame,text="Current",padding=20)
    current_frame.grid(row=0,column=1,padx=10)

    current_value = ttk.Label(current_frame,text="0.00 A",font=("TkDefaultFont",16))
    current_value.pack()

    temperature_frame = ttk.LabelFrame(measurements_frame,text="Temperature",padding=20)
    temperature_frame.grid(row=0,column=2,padx=10)

    temperature_value = ttk.Label(temperature_frame,text="0.00 °C",font=("TkDefaultFont",16))
    temperature_value.pack()

    # CONSOLE

    console_frame = ttk.LabelFrame(main_screen,text="Console",padding=10)
    console_frame.pack(fill="both",expand=True,side="bottom")

    console = Text(console_frame,height=10,state="disabled")
    console.pack(fill="both",expand=True)

    console_write(console,"Connected")
    console_write(console,f"Port: {selected_port}")

    # BUTTONS

    buttons_frame = ttk.Frame(main_screen)
    buttons_frame.pack(pady=20)

    check_files_button = ttk.Button(buttons_frame,text="CHECK FILES ON PICO",command=lambda: check_files_on_pico(selected_port,connection,console))
    check_files_button.pack(side="left",padx=5)

    send_files_button = ttk.Button(buttons_frame,text="SEND FILED TO PICO",command=lambda: select_files(selected_port,connection,console))
    send_files_button.pack(side="left",padx=5)

    start_button = ttk.Button(buttons_frame,text="START CHARACTERISTIC",command=lambda: start_characteristic(connection,voltage_value,current_value,temperature_value,console))
    start_button.pack(side="left",padx=5)

    # CONNECTION MONITOR

    check_connection(selected_port,status_dot,status_label)


def check_files_on_pico(selected_port,connection,console):
    console_write(console,"Checking files on Pico...")

    try:
        if connection.is_open:
            connection.close()
    except Exception as e:
        console_write(console,f"ERROR closing connection: {e}")
        return

    try:
        result = subprocess.run(["mpremote","connect",selected_port,"fs","ls"],capture_output=True,text=True)

        if result.returncode == 0:
            console_write(console,"Files on Pico:")
            output = result.stdout.strip()

            if output:
                for line in output.splitlines():
                    console_write(console,line)
            else:
                console_write(console,"Pico filesystem is empty.")
        else:
            error = result.stderr.strip()

            if not error:
                error = result.stdout.strip()

            console_write(console,"ERROR: Could not check Pico files.")
            console_write(console,error)

    except FileNotFoundError:
        console_write(console,"ERROR: mpremote not found")
        console_write(console,"Install it with: python -m pip install mpremote")
    except Exception as e:
        console_write(console,f"ERROR: {e}")

    try:
        connection.open()
        console_write(console,"Serial connection restored.")
    except Exception as e:
        console_write(console,f"ERROR reopening connection: {e}")


def select_files(selected_port,connection,console):
    files = filedialog.askopenfilenames(title="Select files to send to Pico",filetypes=[("Python files","*.py"),("All files","*.*")])

    if not files:
        return

    console_write(console,"Preparing to send files...")

    try:
        if connection.is_open:
            connection.close()
    except Exception as e:
        console_write(console,f"ERROR closing connection: {e}")
        return

    for file_path in files:
        file_name = os.path.basename(file_path)
        console_write(console,f"Sending {file_name}...")

        try:
            result = subprocess.run(
                ["mpremote","connect",selected_port,"fs","cp",file_path,":"+file_name],
                capture_output=True,text=True)

            if result.returncode == 0:
                console_write(console,f"Sent: {file_name}")
            else:
                error = result.stderr.strip()

                if not error:
                    error = result.stdout.strip()

                console_write(console,f"ERROR: {file_name}")
                console_write(console,error)

        except FileNotFoundError:
            console_write(console,"ERROR: mpremote not found")
            console_write(console,"Install it with: python -m pip install mpremote")
            break
        except Exception as e:
            console_write(console,f"ERROR: {e}")

    console_write(console,"File transfer finished.")

    try:
        connection.open()
        console_write(console,"Serial connection restored.")
    except Exception as e:
        console_write(console,f"ERROR reopening connection: {e}")


def calculate_characteristic_parameters(voltages,currents):
    if not voltages or not currents:
        return None

    powers = []

    for voltage,current in zip(voltages,currents):
        powers.append(voltage * current)

    max_power_index = powers.index(max(powers))

    pmax = powers[max_power_index]
    vmp = voltages[max_power_index]
    imp = currents[max_power_index]

    # ISC

    isc_index = min(range(len(voltages)),key=lambda i: abs(voltages[i]))
    isc = currents[isc_index]

    # VOC

    voc_index = min(range(len(currents)),key=lambda i: abs(currents[i]))
    voc = voltages[voc_index]

    return {"Isc":isc,"Voc":voc,"Pmax":pmax,"Vmp":vmp,"Imp":imp}


def save_characteristic(voltages,currents,temperatures,measurement_time,parameters,console):
    if not voltages:
        messagebox.showwarning("No data","There are no characteristic points to save.")
        return

    file_path = filedialog.asksaveasfilename(
        title="Save characteristic",
        defaultextension=".csv",
        filetypes=[("CSV files","*.csv"),("All files","*.*")]
    )

    if not file_path:
        return

    try:
        with open(file_path,"w",newline="",encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow(["Measurement information"])
            writer.writerow(["Date and time",measurement_time])
            writer.writerow(["Number of points",len(voltages)])

            if parameters:
                writer.writerow(["Isc [A]",parameters["Isc"]])
                writer.writerow(["Voc [V]",parameters["Voc"]])
                writer.writerow(["Pmax [W]",parameters["Pmax"]])
                writer.writerow(["Vmp [V]",parameters["Vmp"]])
                writer.writerow(["Imp [A]",parameters["Imp"]])

            writer.writerow([])
            writer.writerow(["Voltage [V]","Current [A]","Power [W]","Temperature [°C]"])

            for voltage,current,temperature in zip(voltages,currents,temperatures):
                power = voltage * current
                writer.writerow([voltage,current,power,temperature])

        console_write(console,f"Characteristic saved: {file_path}")
        messagebox.showinfo("Saved","Characteristic saved successfully.")

    except Exception as e:
        console_write(console,f"ERROR saving characteristic: {e}")
        messagebox.showerror("Save error",str(e))


def start_characteristic(connection,voltage_value,current_value,temperature_value,console):
    characteristic_window = Toplevel(root)
    characteristic_window.title("I/V Characteristic")
    characteristic_window.geometry("1080x720")

    # DATA

    voltages = []
    currents = []
    temperatures = []

    current_temperature = 0.0
    measurement_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    measurement_running = True

    # GRAPH

    graph_frame = ttk.Frame(characteristic_window,padding=10)
    graph_frame.pack(fill="both",expand=True)

    figure = Figure(figsize=(8,5))
    axis_iv = figure.add_subplot(111)

    axis_iv.set_title("I/V Characteristic")
    axis_iv.set_xlabel("Voltage [V]")
    axis_iv.set_ylabel("Current [A]")
    axis_iv.grid()

    canvas = FigureCanvasTkAgg(figure,master=graph_frame)
    canvas.get_tk_widget().pack(fill="both",expand=True)

    # STATUS

    status_label = ttk.Label(characteristic_window,text="Measuring...")
    status_label.pack(pady=3)

    # PARAMETERS

    parameters_frame = ttk.Frame(characteristic_window)
    parameters_frame.pack(pady=3)

    isc_label = ttk.Label(parameters_frame,text="Isc: -- A")
    isc_label.grid(row=0,column=0,padx=10)

    voc_label = ttk.Label(parameters_frame,text="Voc: -- V")
    voc_label.grid(row=0,column=1,padx=10)

    pmax_label = ttk.Label(parameters_frame,text="Pmax: -- W")
    pmax_label.grid(row=0,column=2,padx=10)

    vmp_label = ttk.Label(parameters_frame,text="Vmp: -- V")
    vmp_label.grid(row=0,column=3,padx=10)

    imp_label = ttk.Label(parameters_frame,text="Imp: -- A")
    imp_label.grid(row=0,column=4,padx=10)

    # GRAPH UPDATE

    def update_graph():
        axis_iv.clear()
        axis_iv.plot(voltages,currents,marker=".")
        axis_iv.set_title("I/V Characteristic")
        axis_iv.set_xlabel("Voltage [V]")
        axis_iv.set_ylabel("Current [A]")
        axis_iv.grid()
        figure.tight_layout()
        canvas.draw()

    # UPDATE PARAMETERS

    def update_parameters():
        parameters = calculate_characteristic_parameters(voltages,currents)

        if not parameters:
            return

        isc_label.config(text=f"Isc: {parameters['Isc']:.3f} A")
        voc_label.config(text=f"Voc: {parameters['Voc']:.3f} V")
        pmax_label.config(text=f"Pmax: {parameters['Pmax']:.3f} W")
        vmp_label.config(text=f"Vmp: {parameters['Vmp']:.3f} V")
        imp_label.config(text=f"Imp: {parameters['Imp']:.3f} A")

    # BUTTONS

    buttons_frame = ttk.Frame(characteristic_window)
    buttons_frame.pack(pady=5)

    save_button = ttk.Button(
        buttons_frame,
        text="SAVE CHARACTERISTIC",
        command=lambda: save_characteristic(
            voltages,
            currents,
            temperatures,
            measurement_time,
            calculate_characteristic_parameters(voltages,currents),
            console
        )
    )
    save_button.pack(side="left",padx=5)

    def stop_characteristic():
        nonlocal measurement_running

        if not measurement_running:
            return

        measurement_running = False

        try:
            connection.write(b"STOP\n")
            console_write(console,"STOP command sent to Pico.")
        except Exception as e:
            console_write(console,f"ERROR sending STOP: {e}")

        status_label.config(text="Measurement stopped")

    stop_button = ttk.Button(buttons_frame,text="STOP",command=stop_characteristic)
    stop_button.pack(side="left",padx=5)

    def close_window():
        nonlocal measurement_running

        if measurement_running:
            stop_characteristic()

        characteristic_window.destroy()

    back_button = ttk.Button(buttons_frame,text="BACK",command=close_window)
    back_button.pack(side="left",padx=5)

    characteristic_window.protocol("WM_DELETE_WINDOW",close_window)

    # START MEASUREMENT

    try:
        connection.reset_input_buffer()
        connection.write(b"START\n")
    except Exception as e:
        measurement_running = False
        status_label.config(text="Connection error")
        console_write(console,f"ERROR: {e}")
        return

    # READ DATA

    def read_data():
        nonlocal current_temperature
        nonlocal measurement_running

        if not characteristic_window.winfo_exists():
            return

        if not measurement_running:
            return

        while connection.in_waiting:
            try:
                line = connection.readline().decode(errors="ignore").strip()
            except Exception as e:
                console_write(console,f"ERROR reading serial data: {e}")
                continue

            if not line:
                continue

            console_write(console,line)

            # TEMPERATURE

            if line.startswith("TEMP,"):
                try:
                    current_temperature = float(line.split(",",1)[1])
                    temperature_value.config(text=f"{current_temperature:.2f} °C")
                except ValueError:
                    console_write(console,f"ERROR: Invalid temperature data: {line}")

                continue

            # FINISHED

            if line == "FINISHED":
                measurement_running = False
                status_label.config(text="Characteristic finished")
                update_parameters()
                continue

            # ERROR FROM PICO

            if line.startswith("ERROR"):
                console_write(console,f"Pico error: {line}")
                continue

            # VOLTAGE,CURRENT

            parts = line.split(",")

            if len(parts) != 2:
                console_write(console,f"Invalid data ignored: {line}")
                continue

            try:
                voltage = float(parts[0])
                current = float(parts[1])
            except ValueError:
                console_write(console,f"Invalid numeric data ignored: {line}")
                continue

            voltages.append(voltage)
            currents.append(current)
            temperatures.append(current_temperature)

            voltage_value.config(text=f"{voltage:.2f} V")
            current_value.config(text=f"{current:.2f} A")

            update_graph()
            update_parameters()

        if measurement_running:
            characteristic_window.after(10,read_data)

    read_data()


def check_connection(selected_port,status_dot,status_label):
    ports = serial.tools.list_ports.comports()
    connected = any(p.device == selected_port for p in ports)

    if connected:
        status_dot.config(foreground="green")
        status_label.config(text=f"Connected  {selected_port}")
    else:
        status_dot.config(foreground="red")
        status_label.config(text="Disconnected")

    root.after(1000,check_connection,selected_port,status_dot,status_label)


def refresh_ports():
    ports = serial.tools.list_ports.comports()
    pico_ports = []

    for port in ports:
        if port.vid == 0x2E8A and port.pid == 0x0005:
            pico_ports.append(port.device)

    port_list["values"] = pico_ports

    if pico_ports:
        port_list.current(0)
    else:
        port_list.set("")


# MAIN WINDOW

root = Tk()
root.title("PV Characteristics")
root.geometry("500x250")

port_screen = ttk.Frame(root,padding=30)
port_screen.pack(fill="both",expand=True)

title_label = ttk.Label(port_screen,text="Select Pico port",font=("TkDefaultFont",16))
title_label.pack(pady=(0,20))

port_list = ttk.Combobox(port_screen,state="readonly")
port_list.pack(pady=5)

refresh_button = ttk.Button(port_screen,text="REFRESH PORTS",command=refresh_ports)
refresh_button.pack(pady=5)

connect_button = ttk.Button(port_screen,text="CONNECT",command=connect)
connect_button.pack(pady=10)

refresh_ports()

root.mainloop()