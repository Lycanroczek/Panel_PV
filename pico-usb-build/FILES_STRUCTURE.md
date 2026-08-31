# Struktura plików projektu - Pico 2 USB

Kompletny przegląd wszystkich plików w projekcie.

## Struktura katalogów

```
/home/marcin/projekt/pico-usb-build/
│
├── 📄 README.md                         ← START HERE (pełna dokumentacja)
├── 📄 QUICKSTART.md                    ← Quick start (5 minut)
├── 📄 ARCH_BUILD.md                    ← Szczegółowe instrukcje Arch Linux
├── 📄 INTEGRATION.md                   ← Integracja z istniejącym projektem
├── 📄 FILES_STRUCTURE.md               ← Ten plik
│
├── 🔨 build.sh                         ← Master build script
│   └── Etapy: deps, sources, configure, build, flash, clean
│
├── 🚀 setup_env.sh                     ← Automatyczne konfigurowanie ENV
│   └── Instaluje zależności, tworzy .env.local
│
├── 📋 manifest.py                      ← Konfiguracja frozen modules
│   └── Definiuje które pliki zamrozić w firmware
│
├── 📊 .env (utworzony automatycznie)
│   └── Zmienne: PICO_SDK_PATH, PICO_TINYUSB_PATH, itp.
│
├── 📂 sources/ (utworzony przez ./build.sh sources)
│   ├── pico-sdk/                       ← Pico SDK v2.3.0
│   │   ├── pico_sdk_init.cmake
│   │   ├── src/rp2_common/
│   │   └── ...
│   │
│   ├── micropython/                    ← MicroPython v1.29.0
│   │   ├── ports/rp2/
│   │   │   ├── CMakeLists.txt
│   │   │   ├── Makefile
│   │   │   ├── boards/
│   │   │   │   ├── RPI_PICO2/         (domyślnie)
│   │   │   │   └── RPI_PICO_W/
│   │   │   └── *.c (port files)
│   │   ├── py/
│   │   └── ...
│   │
│   └── tinyusb/                        ← TinyUSB v0.21.0
│       ├── src/tusb.h
│       ├── src/portable/raspberrypi/
│       │   └── pio_usb/
│       └── ...
│
├── 📂 boards/
│   └── RPI_PICO2_USB/                  ← Custom board config dla RP2350
│       ├── mpconfigboard.cmake         ← GPIO10/11 config
│       ├── mpconfigboard.h             ← USB defines
│       └── mpconfigvariant.cmake       ← RP2350 platform
│
├── 📂 modules/
│   └── usb_device/                     ← C module dla USB CDC
│       ├── usb_module.c                ← Main USB implementation
│       ├── micropython.cmake           ← CMake build config
│       └── micropython.mk              ← Makefile build config
│
├── 📂 examples/
│   ├── USB.py                          ← High-level Python wrapper
│   │   ├── USB class                   ← Prosty interfejs
│   │   └── USBProtocol class           ← Protokół z callback'ami
│   │
│   ├── test_usb.py                     ← Test na Pico (REPL)
│   │   ├── PING/PONG test
│   │   ├── LED control
│   │   └── RS485 forwarding
│   │
│   └── main.py                         ← Example integracji
│       ├── RS485 + USB
│       ├── Command protocol
│       └── Status monitoring
│
├── 📂 firmware/ (utworzony przez build.sh build)
│   ├── firmware_rp2350_usb.uf2         ← Ostateczny firmware (wgrywać na Pico!)
│   └── firmware_rp2350_usb.elf         ← Debug symbol (opcjonalnie)
│
├── 📂 build/ (utworzony przez kompilację)
│   ├── CMakeFiles/
│   ├── cmake_install.cmake
│   └── ...
│
└── 📂 .local/ (opcjonalnie dla zainstalowanych tool'ów)
    └── ...
```

## Opis kluczowych plików

### Główne dokumenty

| Plik | Cel | Czytelnik |
|------|-----|-----------|
| [README.md](README.md) | **Pełna dokumentacja** | Wszyscy |
| [QUICKSTART.md](QUICKSTART.md) | Szybki start 5 minut | Impulsywni użytkownicy |
| [ARCH_BUILD.md](ARCH_BUILD.md) | Krok po kroku dla Arch | Szczegółowcy |
| [INTEGRATION.md](INTEGRATION.md) | Łączenie z RS485/ADC | Integracjoniści |

### Build scripts

| Plik | Opis | Użycie |
|------|------|--------|
| `build.sh` | Master build script | `./build.sh [stage]` |
| `setup_env.sh` | Installer dependencies | `bash setup_env.sh` |
| `manifest.py` | Frozen modules config | Edytuj dla custom kodu |

### Moduł USB

| Plik | Opis |
|------|------|
| `modules/usb_device/usb_module.c` | Implementacja USB CDC w C (~400 linii) |
| `modules/usb_device/micropython.cmake` | CMake config |
| `modules/usb_device/micropython.mk` | Makefile config |

### Python wrappers

| Plik | Opis | Gdzie działa |
|------|------|--------------|
| `examples/USB.py` | High-level wrapper | Na Pico (frozen) |
| `test_pc_usb.py` | PC test tool | Na PC (Linux) |
| `examples/test_usb.py` | Basic REPL test | Na Pico (REPL) |
| `examples/main.py` | RS485 + USB integration | Na Pico (frozen) |

### Konfiguracja hardware

| Plik | Konfiguruje | Zmienne |
|------|-------------|---------|
| `boards/RPI_PICO2_USB/mpconfigboard.cmake` | GPIO pins | `PICO_DEFAULT_PIO_USB_DP_PIN` |
| `boards/RPI_PICO2_USB/mpconfigboard.h` | USB defines | `CFG_TUD_CDC`, itp. |
| `boards/RPI_PICO2_USB/mpconfigvariant.cmake` | Platform (RP2350) | `PICO_PLATFORM` |

## Rozmiary plików (szacunkowe)

| Komponent | Rozmiar | Opis |
|-----------|---------|------|
| Pico SDK | ~200 MB | Pobrany z GitHub |
| MicroPython | ~150 MB | Pobrany z GitHub |
| TinyUSB | ~50 MB | Pobrany z GitHub |
| Firmware (uf2) | ~500 KB | Kompilowany |
| Firmware (elf) | ~1.5 MB | Kompilowany (z debug symbols) |

## Czasem kompilacji (Arch Linux)

| Etap | Czas | Notatki |
|------|------|---------|
| `deps` | <2 min | Pacman updates |
| `sources` | ~5 min | Git clone (zależy od internetu) |
| `configure` | <1 min | Konfiguracja CMake |
| `build` (pierwszy) | ~30-45 min | Build Pico SDK + MP + Module |
| `build` (kolejne) | ~30-60 s | Tylko zmienione pliki |
| `flash` | <5 s | Kopia na dysk Pico |
| `clean` | ~1 min | Usunięcie build'ów |

##Flow pracy

### First-time setup (30-50 minut)

```bash
cd pico-usb-build

# 1. Setup (5 min)
bash setup_env.sh
source .env.local

# 2. Download (5 min)
./build.sh sources

# 3. Configure (<1 min)
./build.sh configure

# 4. Build (20-40 min)
./build.sh build

# 5. Flash (<5 sec)
./build.sh flash

# 6. Test
python3 test_pc_usb.py
```

### Iteracyjna praca (< 1 min)

Po zmianach w kodzie:

```bash
# Tylko przebuduj i wgraj
./build.sh build && ./build.sh flash

# To zajmie ~30-60 sekund
```

### Development (bez wgrywania)

```bash
# Edytuj main.py i wysyłaj z REPL
# Pico czeka na polecenia z REPL:

python3 test_pc_usb.py
# (interaktywne wpisywanie komend)
```

## Modyfikacje custom

### Zmiana GPIO pins (USB)

Edytuj: `boards/RPI_PICO2_USB/mpconfigboard.cmake`

```cmake
set(PICO_DEFAULT_PIO_USB_DP_PIN 10)   # D+ (zmień tutaj)
set(PICO_DEFAULT_PIO_USB_DM_PIN 11)   # D- (zmień tutaj)
```

Przebuduj: `./build.sh build`

### Dodanie własnego Python kodu

```bash
# 1. Dodaj plik
cp my_module.py pico-usb-build/examples/

# 2. Zmrażaj w manifest
echo 'freeze("examples", "my_module.py")' >> pico-usb-build/manifest.py

# 3. Przebuduj
cd pico-usb-build && ./build.sh build && ./build.sh flash
```

### Zmiana buffer size (USB)

Edytuj: `modules/usb_device/usb_module.c`

```c
#define USB_BUFFER_SIZE 256  // Zmień na 512, 1024, itp.
```

Przebuduj: `./build.sh build`

### Wyłączenie modułów (zmniejszenie rozmiaru)

Edytuj: `boards/RPI_PICO2_USB/mpconfigboard.h`

```c
#define MICROPY_PY_NETWORK 0        // Wyłącz network
#define MICROPY_PY_WEBREPL 0        // Wyłącz WebREPL
#define MICROPY_PY_BLUETOOTH 0      // Wyłącz Bluetooth
```

## Pliki ignorowane (w .gitignore)

```
sources/           # Downloaded Pico SDK, MP, TinyUSB
build/             # Build output directory
firmware/          # Compiled firmware
.env               # Environment variables
.venv/             # Python venv
*.o                # Object files
*.a                # Static libraries
__pycache__/       # Python cache
*.pyc              # Compiled Python
```

## Czyszczenie

```bash
# Usuń build output
./build.sh clean

# Usuń wszystko (źródła zostaną)
rm -rf build/ firmware/ .env

# Full reset (włączając źródła!)
rm -rf build/ firmware/ sources/ .env .env.local
```

## Wsparcie plików

Jeśli masz problem z plikiem:

| Problem | Rozwiązanie |
|---------|-------------|
| `usb_module.c` nie kompiluje | Sprawdź `modules/usb_device/micropython.cmake` |
| Pico nie pojawia się na USB | Sprawdź konfigurację w `boards/RPI_PICO2_USB/` |
| Bluetooth/Network błędy | Wyłącz w `mpconfigboard.h` |
| Buffer overflow | Zwiększ `USB_BUFFER_SIZE` w `usb_module.c` |

## Dalsze zasoby

- [MicroPython Docs](https://docs.micropython.org/)
- [Pico SDK Docs](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-c-sdk.pdf)
- [TinyUSB Docs](https://docs.tinyusb.org/)
- [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)

---

**Suma:** ~850 linii kodu C, ~300 linii Python, 5 dokumentów, 7 skryptów
