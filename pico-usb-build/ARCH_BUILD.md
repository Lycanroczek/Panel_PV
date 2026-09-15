# Arch Linux - Instrukcja Budowania Firmware

> Uwaga: wskazane wersje TinyUSB 0.21.0 i Pico-PIO-USB nie tworzą kompletnego
> CDC Device przez PIO na RP2350. Etap build służy obecnie do wykrycia tej
> niezgodności; nie zakładaj, że wynik będzie enumerował jako `/dev/ttyACM*`.

Kompletny, krok po kroku przewodnik dla Arch Linux.

## Krok 1: Przygotowanie systemu

### Aktualizacja systemu

```bash
sudo pacman -Syu
```

### Instalacja wymaganych pakietów

```bash
# Compiler toolchain
sudo pacman -S base-devel git cmake python3

# ARM embedded toolchain
sudo pacman -S arm-none-eabi-gcc arm-none-eabi-gdb \
    arm-none-eabi-binutils arm-none-eabi-newlib

# Narzędzia do wgrywania
sudo pacman -S openocd

# Narzędzia dodatkowe
sudo pacman -S pkg-config libusb
```

### Weryfikacja instalacji

```bash
# Kompilator
arm-none-eabi-gcc --version
# powinno wydrukować: arm-none-eabi-gcc (GCC) ...

cmake --version
python3 --version

openocd --version
```

## Krok 2: Pobranie projektu

```bash
cd /home/marcin/projekt
git clone https://github.com/[twój-repo]/pico-usb-build.git
cd pico-usb-build
chmod +x build.sh
```

## Krok 3: Pobranie źródeł (automatycznie)

```bash
./build.sh sources
```

Lub ręcznie:

```bash
# Utwórz katalog źródeł
mkdir -p sources
cd sources

# Pico SDK
git clone --depth=1 -b 2.3.0 https://github.com/raspberrypi/pico-sdk.git

# MicroPython
git clone --depth=1 -b v1.29.0 https://github.com/micropython/micropython.git

# TinyUSB
git clone --depth=1 -b 0.21.0 https://github.com/hathach/tinyusb.git

# Inicjalizacja submodułów Pico SDK
cd pico-sdk
git submodule update --init --depth=1
cd ..
```

## Krok 4: Konfiguracja zmiennych środowiskowych

Utwórz `.env`:

```bash
cat > .env << 'EOF'
export PICO_SDK_PATH="$(pwd)/sources/pico-sdk"
export PICO_TINYUSB_PATH="$(pwd)/sources/tinyusb"
export MICROPYTHON_DIR="$(pwd)/sources/micropython"
export PICOTOOL_ALLOW_UNSAFE_LIBUSB=1
EOF

# Załaduj zmienne
source .env

# Weryfikuj
echo $PICO_SDK_PATH
echo $PICO_TINYUSB_PATH
```

## Krok 5: Kompilacja firmware (automatycznie)

Najprostsze - użyj skryptu:

```bash
./build.sh build
```

### Lub kompilacja ręczna

```bash
# Załaduj zmienne
source .env

# Przejdź do MicroPython RP2 port
cd sources/micropython/ports/rp2

# Wyczyść stary build
make clean BOARD=RPI_PICO_2

# Kompiluj
make -j$(nproc) \
    BOARD=RPI_PICO_2 \
    USER_C_MODULES="../../../../modules/usb_device/micropython.cmake" \
    FROZEN_MANIFEST="../../../../manifest.py"

# Firmware powinien być w: build-RPI_PICO_2/firmware.uf2
ls -lh build-RPI_PICO_2/firmware.uf2
```

### Opcje kompilacji

| Opcja | Wartość | Opis |
|-------|---------|------|
| `BOARD` | RPI_PICO_2 | Pico 2 (RP2350) |
| `DEBUG` | 0/1 | Symbol debugowania |
| `MICROPY_ENABLE_GC` | 1 | Garbage collection |
| `LTO` | 1 | Link-Time Optimization |

Więcej opcji:

```bash
cd sources/micropython/ports/rp2
cat Makefile | grep -A 50 "^# Customization variables"
```

## Krok 6: Sprawdzenie firmware

```bash
# Rozmiar
ls -lh build-RPI_PICO_2/firmware.uf2

# Strings (szukaj "MicroPython")
arm-none-eabi-objdump -s -j .rodata build-RPI_PICO_2/firmware.elf \
    | grep -A2 "MicroPython"

# Symbole (USB module)
arm-none-eabi-nm build-RPI_PICO_2/firmware.elf | grep usb
```

## Krok 7: Wgrywanie do Pico

### Metoda 1: USB BOOTSEL (rekomendowana)

```bash
# 1. Przytrzymaj BOOTSEL na Pico
# 2. Podłącz USB
# 3. Zwolnij BOOTSEL

sleep 1

# Czekaj aż pojawi się dysk
until [ -d /media/$USER/RPI-RP2 ]; do
    echo "Czekam na Pico..."
    sleep 1
done

# Skopiuj firmware
cp build-RPI_PICO_2/firmware.uf2 /media/$USER/RPI-RP2/

# Czekaj na restartowanie
sleep 2

echo "✓ Firmware wgrany!"
```

Lub:

```bash
./build.sh flash
```

### Metoda 2: OpenOCD (JTAG/SWD)

Wymaga JTAG debuggera (np. CMSIS-DAP, ST-Link).

```bash
# Konfiguracja dla CMSIS-DAP
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg \
    -c "adapter speed 5000" \
    -c "program build-RPI_PICO_2/firmware.elf verify reset exit"

# Lub dla ST-Link v2
openocd -f interface/stlink.cfg -f target/rp2040.cfg \
    -c "adapter speed 1800" \
    -c "program build-RPI_PICO_2/firmware.elf verify reset exit"
```

## Krok 8: Weryfikacja - Testowanie USB

### Sprawdzenie portu szeregowego

```bash
# Wylistuj dostępne porty
ls -la /dev/ttyACM*

# Powinna być tylko nowa instancja
# np. /dev/ttyACM0
```

### Test z minicom

```bash
sudo pacman -S minicom

minicom -D /dev/ttyACM0 -b 115200
```

Polecenia:

```
PING        → PONG
STATUS      → USB:READY RS485:OK
LED_ON      → LED:ON
INFO        → Pico ARM/RP2350
```

Aby wyjść: Ctrl-A, x

### Test z Python

```bash
python3 << 'EOF'
import serial
import time

port = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

# Wyślij PING
port.write(b'PING\n')
time.sleep(0.2)

# Czytaj
response = port.readline()
print(f"Response: {response}")

port.close()
EOF
```

### Test z bashiem

```bash
# Otwórz port (czytanie)
cat /dev/ttyACM0 &
CAT_PID=$!

sleep 1

# Wyślij dane
echo "PING" > /dev/ttyACM0

sleep 1

# Zabij czytanie
kill $CAT_PID 2>/dev/null
```

## Krok 9: Debugowanie

### Jeśli firmware się nie pojawia

Sprawdź czy Pico jest naprawdę w trybie BOOTSEL:

```bash
dmesg | tail -20
# Powinno być: "Pico" / "RP2040" / "New USB device found"
```

### Jeśli Pico nie pojawia się na /dev/ttyACM*

```bash
# Sprawdź lsusb
lsusb | grep -i pico

# Powinna być: "Bus XXX Device YYY: ID XXXX:XXXX 
# Raspberry Pi Pico 2"
```

### Logowanie USB na Linux

```bash
# Włącz debug dla cdc_acm
echo module cdc_acm +p > /sys/kernel/debug/dynamic_debug/control

# Czytaj logi
sudo journalctl -f -k

# Wyślij dane
echo "TEST" > /dev/ttyACM0
```

### Jeśli kompilacja się nie powiedzie

```bash
# Wyczyść wszystko
make distclean BOARD=RPI_PICO_2

# Sprawdź zmienne
echo "PICO_SDK_PATH=$PICO_SDK_PATH"
echo "PICO_TINYUSB_PATH=$PICO_TINYUSB_PATH"

# Przebiegnij configure
./build.sh configure

# Spróbuj ponownie
./build.sh build 2>&1 | tail -50
```

## Krok 10: Dostosowanie (opcjonalnie)

### Zmiana prędkości baud

W `examples/test_usb.py` zmień:

```python
# Domyślnie 115200 (nie istnieje - USB CDC)
# USB CDC automatycznie dopasowuje się do PC
```

### Zmiana GPIO pins

W `boards/RPI_PICO2_USB/mpconfigboard.cmake`:

```cmake
set(PICO_DEFAULT_PIO_USB_DP_PIN 10)   # Zmień tutaj
set(PICO_DEFAULT_PIO_USB_DM_PIN 11)   # I tutaj
```

### Zmiana rozmiaru buffer

W `modules/usb_device/usb_module.c`:

```c
#define USB_BUFFER_SIZE 256  // Zmień rozmiar
```

Następnie:

```bash
./build.sh clean
./build.sh build
./build.sh flash
```

## Krok 11: Integracja z projektem

Skopiuj do `main.py`:

```bash
cp examples/main.py /home/marcin/projekt/main.py
cp examples/USB.py /home/marcin/projekt/USB.py
```

Edytuj `main.py`, aby zintegrować z twoimi modułami:

```python
from RS485 import RS485Modbus  # Twój moduł
from USB import USB

# ... reszta kodu
```

## Troubleshooting

### Problem: "arm-none-eabi-gcc: command not found"

```bash
sudo pacman -S arm-none-eabi-gcc
```

### Problem: "PICO_SDK_PATH not found"

```bash
source .env
echo $PICO_SDK_PATH
ls $PICO_SDK_PATH/pico_sdk_init.cmake
```

### Problem: "CMake Error: CMAKE_C_COMPILER not set"

```bash
# Upewnij się że arm-none-eabi-gcc jest zainstalowany
which arm-none-eabi-gcc

# Ustaw ścieżkę
export CMAKE_C_COMPILER=$(which arm-none-eabi-gcc)
export CMAKE_CXX_COMPILER=$(which arm-none-eabi-g++)
```

### Problem: Blędy podczas wgrywania

```bash
# Pewne, że Pico jest w BOOTSEL? (LED nie powinno być włączone)
# Spróbuj inny kabel USB
# Spróbuj inny port USB

# Linux - unmount dysk jeśli się pojawił wcześniej
sudo umount /media/$USER/RPI-RP2 2>/dev/null || true

# Spróbuj ponownie wgrywania
./build.sh flash
```

## Wsparcie

- GitHub Issues: https://github.com/raspberrypi/pico-sdk/issues
- MicroPython Forum: https://forum.micropython.org/
- Arch AUR (dla nowszych wersji): https://aur.archlinux.org/packages/arm-none-eabi-gcc

## Dalsze kroki

Po udanym wgraniu:

1. Testuj USB z `test_usb.py`
2. Zintegruj z `RS485.py`
3. Opracuj `main.py` dla twojej aplikacji
4. Dodaj CRC / enkrypcję jeśli potrzeba

Powodzenia!
