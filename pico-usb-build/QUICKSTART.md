# Pico 2 USB - Quick Start (5 minut)

Szybki start do skompilowania i przetestowania firmware.

## Założenia
- Arch Linux
- Raspberry Pi Pico 2 (RP2350)
- Kabel USB do dataów
- Zainstalowany Python 3 i git

## Krok 1: Setup (1 min)

```bash
cd /home/marcin/projekt/pico-usb-build

# Zainstaluj zależności (potrzebne dosłownie raz)
bash setup_env.sh

# Załaduj zmienne
source .env.local
```

## Krok 2: Pobierz źródła (2 min)

```bash
./build.sh sources
```

Pobierze:
- Pico SDK
- MicroPython
- TinyUSB

## Krok 3: Kompiluj (1 min)

```bash
./build.sh build
```

Firmware będzie w: `firmware/firmware_rp2350_usb.uf2`

## Krok 4: Wgraj na Pico (1 min)

**W Pico:**
1. Przytrzymaj BOOTSEL
2. Podłącz USB
3. Zwolnij BOOTSEL

**W terminalu:**
```bash
./build.sh flash
```

Lub skopiuj ręcznie:
```bash
cp firmware/firmware_rp2350_usb.uf2 /media/$USER/RPI-RP2/
```

## Krok 5: Test (instant)

```bash
# Sprawdź port
ls /dev/ttyACM*

# Test (Linux)
python3 test_pc_usb.py

# Test (minicom)
minicom -D /dev/ttyACM0 -b 115200
```

Wyślij `PING` - powinna wrócić `PONG`

## Gotowe! 🎉

Firmware jest zainstalowany. Teraz:

1. **Edytuj kod MicroPython:**
   - `examples/test_usb.py` - test USB
   - `examples/USB.py` - wrapper dla `usb_device`
   - `examples/main.py` - integracja z RS485

2. **Zintegruj z RS485:**
   ```python
   from USB import USB
   from RS485 import RS485Modbus
   
   USB.init()
   rs485 = RS485Modbus(...)
   ```

3. **Wgraj swój kod:**
   - Umieść Python w `examples/`
   - W `manifest.py` dodaj: `freeze("examples", "mycode.py")`
   - Przebuduj: `./build.sh build && ./build.sh flash`

## Rozwiązywanie problemów

### Pico nie pojawia się na USB

```bash
dmesg | grep -i pico
lsusb | grep -i pico
```

Jeśli nic nie ma:
- Sprawdź kabel USB (data+power, nie tylko charging)
- Spróbuj inny port USB
- Przebiegnij: `./build.sh flash` ponownie

### Firmware kompiluje się 30+ minut

Normalnie! Pierwsze budowanie zajmuje długo (kompiluje Pico SDK, TinyUSB, MicroPython).

Kolejne budowania będą szybsze (~30-60 sekund).

### Port USB nie otwiera się

```bash
# Sprawdź uprawnienia
ls -la /dev/ttyACM0

# Dodaj użytkownika do grupy dialout
sudo usermod -aG dialout $USER

# Zaloguj się ponownie lub
newgrp dialout
```

## Pliki konfiguracyjne

Jeśli chcesz zmienić GPIO pins, zmień w:

```
boards/RPI_PICO2_USB/mpconfigboard.cmake
```

Zmień:
```cmake
set(PICO_DEFAULT_PIO_USB_DP_PIN 10)   # ← D+
set(PICO_DEFAULT_PIO_USB_DM_PIN 11)   # ← D-
```

Następnie przebuduj: `./build.sh clean && ./build.sh build`

## API użytkownika

### Niski poziom (C module)

```python
import usb_device

usb_device.init()
usb_device.write(b"hello")
data = usb_device.read(256)
```

### Wysoki poziom (wrapper)

```python
from USB import USB

USB.init()
USB.write(b"hello")
data = USB.read()
```

## Dokumentacja

Pełna dokumentacja w [README.md](README.md)

Instrukcje dla Arch Linux: [ARCH_BUILD.md](ARCH_BUILD.md)

## Dalej?

- Modyfikuj `examples/main.py` dla swojej aplikacji
- Dodaj CRC/enkrypcję jeśli potrzeba
- Wdrażaj U/I charakterystyki
- Integruj z PC GUI

---

**Potrzebujesz pomocy?** Patrz [README.md](README.md) lub [ARCH_BUILD.md](ARCH_BUILD.md)
