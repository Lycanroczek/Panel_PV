# Integracja z istniejącym projektem

Jak zintegrować USB module z twoim istniejącym projektem (RS485, menu, ADC).

## Struktura projektu

Obecna struktura w `/home/marcin/projekt/`:

```
projekt/
├── main.py                 # Main application
├── RS485.py               # RS485 UART communication
├── temp_sensor.py         # Temperature sensor
├── expansion_card.py      # Expansion card
├── ADC.py                 # ADC driver
├── menu.py                # Menu system
├── build/                 # Build files
│   └── main/
└── .venv/                 # Virtual environment
```

Nowa struktura z USB:

```
projekt/
├── main.py                    # ← Updated to use USB
├── RS485.py                   # Unchanged
├── temp_sensor.py             # Unchanged
├── expansion_card.py          # Unchanged
├── ADC.py                     # Unchanged
├── menu.py                    # Unchanged
│
├── USB.py                     # ← NEW: USB wrapper
├── usb_protocol.py           # ← NEW: Protocol handler (optional)
│
├── pico-usb-build/           # ← NEW: Firmware directory
│   ├── sources/              #  (Pico SDK, MicroPython, TinyUSB)
│   ├── modules/
│   │   └── usb_device/       #  (USB C module)
│   ├── firmware/
│   │   └── firmware.uf2      #  (Built firmware)
│   ├── build.sh
│   └── ...
```

## Krok 1: Skopiuj USB module

```bash
# Z pico-usb-build do głównego projektu
cp pico-usb-build/examples/USB.py /home/marcin/projekt/

# Opcjonalnie - protocol handler
cp pico-usb-build/examples/USB.py /home/marcin/projekt/usb_protocol.py
```

## Krok 2: Zmodyfikuj main.py

Obecny `main.py`:

```python
# main.py - STARA WERSJA
import time
from RS485 import RS485Modbus
from menu import MenuSystem

def main():
    rs485 = RS485Modbus(...)
    menu = MenuSystem()
    
    while True:
        menu.update()
        time.sleep(0.01)
```

Nowa wersja z USB:

```python
# main.py - NOWA WERSJA
import time
from RS485 import RS485Modbus
from menu import MenuSystem
from USB import USB, USBProtocol  # ← NEW

def main():
    # Initialize RS485
    rs485 = RS485Modbus(
        uart_id=0,
        tx_pin=0,
        rx_pin=1,
        de_pin=5,
        baudrate=9600
    )
    print("[RS485] OK")
    
    # Initialize USB
    USB.init()  # ← NEW
    print("[USB] Initialized on GPIO10/11")
    
    # Initialize menu
    menu = MenuSystem()
    print("[MENU] Ready")
    
    # USB command handler
    def handle_usb_cmd(cmd):  # ← NEW
        cmd = cmd.strip().upper()
        
        if cmd == "PING":
            return "PONG"
        elif cmd == "STATUS":
            return f"USB:OK RS485:OK MENU:OK"
        elif cmd == "HELP":
            return "PING, STATUS, HELP, RS485:*"
        elif cmd.startswith("RS485:"):
            # Forward to RS485
            msg = cmd[6:]
            rs485.send(msg.encode())
            return "RS485:SENT"
        else:
            return f"UNKNOWN: {cmd}"
    
    protocol = USBProtocol(on_command=handle_usb_cmd)  # ← NEW
    
    # Main loop
    while True:
        try:
            # Update USB
            if USB.is_connected():  # ← NEW
                protocol.process()  # ← NEW
            
            # Update RS485
            if rs485.available():
                data = rs485.receive()
                if USB.is_connected():  # ← NEW
                    USB.write(b"RS485:" + data + b"\n")
            
            # Update menu
            menu.update()
            
            time.sleep(0.001)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"ERROR: {e}")
    
    # Cleanup
    USB.deinit()  # ← NEW
    rs485.close()

if __name__ == "__main__":
    main()
```

## Krok 3: Firmware integracji

Firmware zawiera moduł `usb_device`. Po zainstalowaniu firmware będzie dostępny:

```python
# W Pico (na firmware'u)
import usb_device

usb_device.init()
data = usb_device.read(256)
```

Lub używając wrappera:

```python
# Przed wgraniem firmware - dodaj USB.py do Pico
from USB import USB  # ← Ten plik z repo

USB.init()
data = USB.read()
```

## Krok 4: Zintegruj z temperaturą / ADC

Jeśli wysyłasz pomiary U/I przez USB:

```python
# main.py - fragment
from ADC import ADCDriver
from USB import USB

adc = ADCDriver()

while True:
    # Mierz napięcie i prąd
    voltage = adc.read_voltage()  # Your method
    current = adc.read_current()  # Your method
    
    # Wyślij na USB
    if USB.is_ready():
        msg = f"MEAS:{voltage:.2f}V,{current:.2f}A\n"
        USB.write(msg.encode())
    
    time.sleep(0.1)
```

## Krok 5: PC-side - odczyt pomiarów

Plik `test_pc_usb.py` już obsługuje:

```bash
python3 pico-usb-build/test_pc_usb.py /dev/ttyACM0
```

Lub napisy własny script Python:

```python
# pc_client.py
import serial
import time

port = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

while True:
    # Wyślij polecenie pomiaru
    port.write(b'MEAS\n')
    
    # Czekaj odpowiedź
    response = port.readline()
    if response:
        print(response.decode())
    
    time.sleep(1)

port.close()
```

## Krok 6: Build integracji

Aby dodać swój kod do firmware (zamiast na REPL):

### Opcja A: Frozen code (prekomilowany)

```bash
# 1. Skopiuj main.py do pico-usb-build/examples/
cp main.py pico-usb-build/examples/

# 2. Edytuj manifest.py
cat >> pico-usb-build/manifest.py << 'EOF'
freeze("examples", "main.py")
freeze("examples", "RS485.py")
freeze("examples", "USB.py")
EOF

# 3. Przebuduj firmware
cd pico-usb-build
./build.sh build
./build.sh flash
```

### Opcja B: Kod na REPL (dynamiczny)

```python
# Pico - REPL
from RS485 import RS485Modbus
from USB import USB

# ... main() ...
```

Zmień konfigurację w pico-usb-build/manifest.py:

```python
# manifest.py
include("$(PORT_DIR)/boards/manifest.py")
c_module("modules/usb_device")

# Nie zamraź - pozwól na interaktywny kod
# freeze("examples", "main.py")
```

Przebuduj, wgraj, a potem wysyłaj kod z REPL lub przez sieć.

## Kompatybilność

| Moduł | Status | Notatki |
|-------|--------|---------|
| RS485.py | ✓ Kompatybilny | Zmiana: Import USB opcjonalny |
| temp_sensor.py | ✓ Kompatybilny | Brak zmian |
| expansion_card.py | ✓ Kompatybilny | Brak zmian |
| ADC.py | ✓ Kompatybilny | Brak zmian |
| menu.py | ✓ Kompatybilny | Dodaj obsługę USB commandów |

## GPIO zajęte przez USB

| GPIO | Funkcja | Opis |
|------|---------|------|
| 10 | USB D+ | PIO-USB Data Plus |
| 11 | USB D- | PIO-USB Data Minus |
| 12 | VBUSEN | VBUS Enable (opcjonalnie) |

**Pozostałe GPIO są dostępne:**
- 0, 1: UART0 (RS485)
- 2-4: ADC/inne
- 5: GPIO (RS485 DE)
- 6-9: Dostępne
- 13-28: Dostępne
- 25: LED

## Przykłady komunikacji

### PING/PONG

```
PC → Pico: PING\n
Pico → PC: PONG\n
```

### Pomiary U/I

```
PC → Pico: MEAS\n
Pico → PC: MEAS:230V,5.2A\n
```

### Status

```
PC → Pico: STATUS\n
Pico → PC: STATUS:RS485_OK,USB_READY,ADC_OK\n
```

### Komenda do RS485

```
PC → Pico: RS485:0x01,0x03,0x00,0x00,0x00,0x0A\n
Pico → PC: RS485:0x01,0x03,0x14,...\n (odpowiedź z Modbus slave'a)
```

## Debugging

Jeśli USB nie działa:

```python
# W REPL na Pico
import usb_device
usb_device.init()
print(usb_device.is_ready())  # Should be True
print(usb_device.is_connected())  # Should be True
```

Jeśli port się nie pojawia na PC:

```bash
# Linux
lsusb | grep -i pico
dmesg | tail

# Archlinux
udevadm monitor  # Wtedy podłącz Pico
```

## Podsumowanie integracji

1. ✓ Skopiuj `USB.py` do projektu
2. ✓ Zmodyfikuj `main.py` do użycia USB
3. ✓ Zbuduj firmware: `./build.sh build`
4. ✓ Wgraj firmware: `./build.sh flash`
5. ✓ Testuj: `python3 test_pc_usb.py`

Done! 🎉
