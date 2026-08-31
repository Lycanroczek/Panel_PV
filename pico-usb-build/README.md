# Raspberry Pi Pico 2 (RP2350) - USB CDC Device via GPIO10/11

Kompletny projekt firmware MicroPython z modułem USB CDC dla Raspberry Pi Pico 2 (RP2350).

## Architektura

- **Główna logika**: MicroPython
- **USB CDC**: C module (`usb_device`) + TinyUSB + PIO-USB
- **GPIO**: USB D+ na GPIO10, USB D- na GPIO11
- **Interfejs Python**: Prosty `USB.read()`, `USB.write()`, `USB.is_ready()`
- **Integracja**: Niezależy od RS485 (osobny moduł)

## Wymagania

### Hardware
- Raspberry Pi Pico 2 (RP2350)
- Kabel USB (do zasilania i BOOTSEL)
- Przewody do podłączenia D+/D- do GPIO10/GPIO11 (opcjonalnie - do testowania na innym Pico)

### Software (Arch Linux)
```bash
sudo pacman -S git curl cmake python3 gcc arm-none-eabi-gcc \
    arm-none-eabi-gdb arm-none-eabi-binutils arm-none-eabi-newlib \
    openocd pkg-config
```

## Szybki start

### 1. Przygotowanie katalogu

```bash
cd /home/marcin/projekt/pico-usb-build
chmod +x build.sh
```

### 2. Instalacja zależności (jeden raz)

```bash
./build.sh deps
```

### 3. Pobranie źródeł

```bash
./build.sh sources
```

To pobierze:
- Pico SDK v2.3.0
- MicroPython v1.29.0  
- TinyUSB v0.21.0

### 4. Konfiguracja toolchaina

```bash
./build.sh configure
```

### 5. Kompilacja firmware

```bash
./build.sh build
```

Firmware zostanie stworzony w `firmware/firmware_rp2350_usb.uf2`

### 6. Wgranie do Pico

```bash
# Przytrzymaj BOOTSEL na Pico
# Podłącz USB
# Zwolnij BOOTSEL po momencie
./build.sh flash
```

Albo ręcznie - skopiuj `firmware/firmware_rp2350_usb.uf2` na dysk Pico.

## Detalna instrukcja

### Wgrywanie firmware (metoda 1: USB)

1. **Przytrzymaj przycisk BOOTSEL** na Pico 2
2. **Podłącz USB do komputera** (LXC/ZEMU może wymagać dodatkowej konfiguracji)
3. **Zwolnij BOOTSEL** - Pico powinno się pojawić jako dysk RPI-RP2

Na Linux:
```bash
# Odczekaj chwilę aż dysk się zmontuje
ls -la /media/$USER/  # Powinno być RPI-RP2

# Skopiuj firmware
cp firmware/firmware_rp2350_usb.uf2 /media/$USER/RPI-RP2/

# Pico automatycznie restartuje się po kopii
sleep 2
```

### Wgrywanie firmware (metoda 2: OpenOCD/JTAG)

Jeśli masz JTAG debugger:

```bash
cd firmware
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg \
    -c "adapter speed 5000" \
    -c "program firmware_rp2350_usb.elf verify reset exit"
```

### Testowanie USB

Po wgraniu firmware, Pico powinno się pojawić jako urządzenie USB CDC (wirtualny port szeregowy):

```bash
# Linux - szukaj /dev/ttyACM*
ls -la /dev/ttyACM*

# Czytanie z Pico
cat /dev/ttyACM0

# Wysłanie danych
echo "PING" > /dev/ttyACM0
```

Lub Python:

```python
import serial

port = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

# Wyślij PING
port.write(b'PING\n')

# Czytaj odpowiedź
print(port.readline())  # b'PONG\n'

port.close()
```

## Struktura projektu

```
pico-usb-build/
├── build.sh                          # Master build script
├── manifest.py                       # Frozen modules config
├── boards/
│   └── RPI_PICO2_USB/
│       ├── mpconfigboard.cmake       # GPIO10/11 config
│       ├── mpconfigvariant.cmake     # RP2350 platform
│       └── mpconfigboard.h           # USB defines
├── modules/
│   └── usb_device/
│       ├── usb_module.c              # USB CDC module
│       ├── micropython.cmake         # Build config (CMake)
│       └── micropython.mk            # Build config (Makefile)
├── examples/
│   ├── USB.py                        # High-level USB wrapper
│   ├── test_usb.py                   # Test script
│   └── main.py                       # Integration example
├── firmware/                         # Output
│   └── firmware_rp2350_usb.uf2      # Final firmware
└── sources/                          # Downloaded sources
    ├── pico-sdk/
    ├── micropython/
    └── tinyusb/
```

## MicroPython API - Moduł `usb_device` (niski poziom)

```python
import usb_device

# Inicjalizacja
usb_device.init()

# Status
is_ready = usb_device.is_ready()        # bool - czy urządzenie gotowe
is_connected = usb_device.is_connected()  # bool - czy USB połączone
bytes_avail = usb_device.any()           # int - ile bajtów do czytania

# I/O
data = usb_device.read(256)              # bytes - odczytaj max 256 bajtów
line = usb_device.read_line()            # bytes - czytaj do \n
written = usb_device.write(b"hello")     # int - ile bajtów wysłanych
written = usb_device.write_str("hello")  # int - wysłanie string

# Control
usb_device.flush()                       # Flush output buffer
usb_device.deinit()                      # Zamknij USB
```

## Python API - Klasa `USB` (wysoki poziom)

```python
from USB import USB

# Inicjalizacja
USB.init()

# Status
if USB.is_ready():
    print("USB gotowy")

# Czytanie
if USB.any() > 0:
    data = USB.read()          # bytes - odczytaj dostępne
    line = USB.read_line()     # bytes - do \n
    text = USB.read_string()   # str - dekoduj UTF-8

# Pisanie
USB.write(b"binary data")      # bytes
USB.write_line("text\n")       # str + newline

# Czyszczenie
USB.flush()
USB.deinit()
```

## Python API - Klasa `USBProtocol` (protokół)

```python
from USB import USBProtocol, USB

def my_handler(cmd):
    if cmd == "PING":
        return "PONG"
    return f"ECHO: {cmd}"

protocol = USBProtocol(on_command=my_handler)

# W main loop
while True:
    protocol.process()
    time.sleep(0.01)
```

## Protokół komunikacji

Wiadomości są tekstowe, kończone `\n`:

```
PC -> Pico:  PING\n
Pico -> PC:  PONG\n

PC -> Pico:  STATUS\n
Pico -> PC:  USB:READY RS485:OK\n

PC -> Pico:  LED_ON\n
Pico -> PC:  LED:ON\n
```

Brak CRC ani szyfrowania (na razie).

## Konfiguracja GPIO

| GPIO | Funkcja | Opis |
|------|---------|------|
| 10  | USB D+ | Data Plus line |
| 11  | USB D- | Data Minus line |
| 12  | VBUSEN (opt.) | VBUS Enable |
| 0, 1 | UART0 | RS485 TX/RX |
| 5   | GPIO | RS485 DE (Drive Enable) |
| 25  | LED | Built-in LED |

## Rozwiązywanie problemów

### Pico nie pojawia się w /dev/ttyACM*

1. Sprawdź czy Pico jest w trybie BOOTSEL
2. Sprawdź w `dmesg`:
   ```bash
   dmesg | tail -20
   ```
3. Zweryfikuj kabel USB (może być charging-only)

### Błąd: "Timeout waiting for USB connection"

- Pico może nie być zasilone - sprawdź zasilanie USB
- GPIO10/11 mogą nie być dostępne - sprawdź pinout
- Spróbuj przebudować: `./build.sh clean && ./build.sh build`

### Błąd kompilacji: "PICO_SDK_PATH not found"

```bash
# Sprawdź zmienne
source .env
echo $PICO_SDK_PATH

# Przebiegnij configure
./build.sh configure
```

### Dane binarysę na USB nie działają

MicroPython USB moduł obsługuje binarne dane w `usb_device.write()`, ale wysyłanie na PC może wymagać odpowiedniej obsługi:

```python
# Prawidłowo
USB.write(b'\x00\x01\x02')  # bytes

# Błędnie
USB.write('\x00\x01\x02')   # string - będzie konwertować
```

## Optymalizacja

### Zmniejszenie rozmiaru firmware

```bash
# Usuń nieznane moduły z boards/RPI_PICO2_USB/mpconfigboard.h
# np. MICROPY_PY_WEBREPL = 0
./build.sh build
```

### Zwiększenie szybkości USB

RP2350 domyślnie pracuje na 150 MHz, co jest optimalne dla PIO-USB.

### Zmniejszenie zużycia energii

```python
# W main.py
import machine
machine.freq(50_000_000)  # Zmniejsz do 50 MHz (oszczędzaj energię)
# USB będzie wolniejszy!
```

## Integracja z RS485

Patrz `examples/main.py` - integruje USB i RS485 w jednej aplikacji:

```python
from RS485 import RS485Modbus
from USB import USB

rs485 = RS485Modbus(uart_id=0, de_pin=5)
USB.init()

while True:
    # Odczytaj z RS485, wyślij na USB
    if rs485.available():
        USB.write(b"RS485:" + rs485.receive() + b"\n")
```

## Wsparcie techniczne

- MicroPython: https://docs.micropython.org/
- Pico SDK: https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-c-sdk.pdf
- TinyUSB: https://docs.tinyusb.org/
- RP2350: https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf

## Licencja

Projekt MicroPython: MPL 2.0  
Pico SDK: BSD 3-Clause  
TinyUSB: MIT  
Kod waszego projektu: Wasza licencja
