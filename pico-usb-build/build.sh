#!/bin/bash
#==============================================================================
# Raspberry Pi Pico 2 (RP2350) MicroPython + USB CDC via GPIO10/11
# Build script for Arch Linux
# Wykonanie: bash build.sh [stage]
# Dostępne etapy: deps, sources, configure, build, flash, clean
#==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
SOURCES_DIR="$PROJECT_ROOT/sources"
MODULES_DIR="$PROJECT_ROOT/modules"
OUTPUT_DIR="$PROJECT_ROOT/firmware"
INSTALL_PREFIX="$PROJECT_ROOT/.local"

# Wersje
PICO_SDK_VER="2.3.0"
TINYUSB_VER="0.21.0"
MICROPYTHON_VER="1.29.0"
PIO_USB_REPO="https://github.com/sekigon-gonnoc/Pico-PIO-USB.git"
PIO_USB_COMMIT="5a37a66dc5d3fbe0ef3cdbeda923a757440f984f"
PIO_USB_DIR="$SOURCES_DIR/Pico-PIO-USB"
BOARD="RPI_PICO2_USB"

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

#==============================================================================
# FUNKCJE POMOCNICZE
#==============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║ $1${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}\n"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "Nie znaleziono polecenia: $1"
        return 1
    fi
    return 0
}

check_program() {
    local prog=$1
    local package=${2:-$1}
    
    if ! check_command "$prog"; then
        log_warn "Instalowanie $package..."
        if ! sudo pacman -S --noconfirm "$package" 2>/dev/null; then
            log_error "Nie udało się zainstalować $package"
            return 1
        fi
    fi
    return 0
}

#==============================================================================
# STAGE 1: INSTALACJA ZALEŻNOŚCI
#==============================================================================

stage_deps() {
    log_step "STAGE 1: Sprawdzanie i instalowanie zależności"
    
    log_info "Sprawdzanie narzędzi..."
    
    # Required tools
    local tools=("git" "curl" "wget" "cmake" "python3" "gcc" "arm-none-eabi-gcc" "openocd" "pkg-config")
    
    for tool in "${tools[@]}"; do
        if ! check_command "$tool"; then
            case "$tool" in
                "arm-none-eabi-gcc")
                    log_warn "Instalowanie arm-none-eabi-toolchain..."
                    sudo pacman -S --noconfirm arm-none-eabi-gcc arm-none-eabi-gdb arm-none-eabi-binutils arm-none-eabi-newlib
                    ;;
                "openocd")
                    log_warn "Instalowanie openocd..."
                    sudo pacman -S --noconfirm openocd
                    ;;
                *)
                    log_error "Brakuje narzędzia: $tool"
                    return 1
                    ;;
            esac
        fi
    done
    
    log_info "✓ Wszystkie zależności spełnione"
}

#==============================================================================
# STAGE 2: POBRANIE ŹRÓDEŁ
#==============================================================================

stage_sources() {
    log_step "STAGE 2: Pobieranie źródeł z GitHub"
    
    mkdir -p "$SOURCES_DIR"
    cd "$SOURCES_DIR"
    
    # Pico SDK
    if [ ! -d "pico-sdk/.git" ]; then
        log_info "Klonowanie Pico SDK v${PICO_SDK_VER}..."
        git clone --depth=1 -b $PICO_SDK_VER https://github.com/raspberrypi/pico-sdk.git pico-sdk
    fi
    
    # TinyUSB
    if [ ! -d "tinyusb/.git" ]; then
        log_info "Klonowanie TinyUSB v${TINYUSB_VER}..."
        git clone --depth=1 -b $TINYUSB_VER https://github.com/hathach/tinyusb.git tinyusb
    fi
    
    # MicroPython
    if [ ! -d "micropython/.git" ]; then
        log_info "Klonowanie MicroPython v${MICROPYTHON_VER}..."
        git clone --depth=1 -b v$MICROPYTHON_VER https://github.com/micropython/micropython.git micropython
    fi

    if [ ! -d "$PIO_USB_DIR/.git" ]; then
        log_info "Klonowanie Pico-PIO-USB..."
        git clone --depth=1 "$PIO_USB_REPO" "$PIO_USB_DIR"
    fi
    git -C "$PIO_USB_DIR" fetch --depth=1 origin "$PIO_USB_COMMIT"
    git -C "$PIO_USB_DIR" checkout --detach "$PIO_USB_COMMIT"
    if ! grep -q "pio_usb_tinyusb_setup_received" "$PIO_USB_DIR/src/pio_usb_device.c"; then
        git -C "$PIO_USB_DIR" apply "$PROJECT_ROOT/patches/pico-pio-usb-tinyusb-hooks.patch"
    fi
    
    log_info "Inicjalizowanie submodułów Pico SDK..."
    cd pico-sdk
    git submodule update --init --depth=1
    cd ..

    mkdir -p "$SOURCES_DIR/micropython/ports/rp2/boards/$BOARD"
    cp "$PROJECT_ROOT/boards/$BOARD"/* "$SOURCES_DIR/micropython/ports/rp2/boards/$BOARD/"
    cd "$SOURCES_DIR/micropython/ports/rp2"
    make BOARD="$BOARD" submodules
    cd "$SOURCES_DIR/micropython"
    rm -rf lib/tinyusb
    ln -s "$SOURCES_DIR/tinyusb" lib/tinyusb
    cd "$SOURCES_DIR"
    
    log_info "✓ Wszystkie źródła pobrane do $SOURCES_DIR"
}

#==============================================================================
# STAGE 3: KONFIGURACJA TOOLCHAINA
#==============================================================================

stage_configure() {
    log_step "STAGE 3: Konfiguracja Pico SDK i toolchaina"
    
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Export zmiennych środowiskowych
    export PICO_SDK_PATH="$SOURCES_DIR/pico-sdk"
    export PICO_TINYUSB_PATH="$SOURCES_DIR/tinyusb"
    export MICROPYTHON_DIR="$SOURCES_DIR/micropython"
    
    log_info "PICO_SDK_PATH: $PICO_SDK_PATH"
    log_info "PICO_TINYUSB_PATH: $PICO_TINYUSB_PATH"
    log_info "MICROPYTHON_DIR: $MICROPYTHON_DIR"
    
    # Weryfikacja
    if [ ! -f "$PICO_SDK_PATH/pico_sdk_init.cmake" ]; then
        log_error "Błąd: Pico SDK nie znaleziony w $PICO_SDK_PATH"
        return 1
    fi
    
    if [ ! -f "$PICO_TINYUSB_PATH/src/tusb.h" ]; then
        log_error "Błąd: TinyUSB nie znaleziony w $PICO_TINYUSB_PATH"
        return 1
    fi
    
    log_info "✓ Konfiguracja toolchaina ukończona"
    
    # Zapisz zmienne do pliku .env
    cat > "$PROJECT_ROOT/.env" << 'EOF'
export PICO_SDK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/sources/pico-sdk" && pwd)"
export PICO_TINYUSB_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/sources/tinyusb" && pwd)"
export MICROPYTHON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/sources/micropython" && pwd)"
export PICOTOOL_ALLOW_UNSAFE_LIBUSB=1
EOF
    
    log_info "✓ Zmienne środowiskowe zapisane do .env"
}

#==============================================================================
# STAGE 4: BUILD FIRMWARE
#==============================================================================

stage_build() {
    log_step "STAGE 4: Kompilowanie firmware"
    
    # Załaduj zmienne
    if [ -f "$PROJECT_ROOT/.env" ]; then
        source "$PROJECT_ROOT/.env"
    fi
    
    export PICO_SDK_PATH="$SOURCES_DIR/pico-sdk"
    export PICO_TINYUSB_PATH="$SOURCES_DIR/tinyusb"
    export MICROPYTHON_DIR="$SOURCES_DIR/micropython"
    
    cd "$SOURCES_DIR/micropython/ports/rp2"
    
    log_info "Czyszczenie starego buildu..."
    make clean BOARD="$BOARD" > /dev/null 2>&1 || true
    
    log_info "Kompilowanie MicroPython dla $BOARD..."
    
    # Build with custom USB module
    make -j$(nproc) \
        BOARD="$BOARD" \
        USER_C_MODULES="$MODULES_DIR/usb_device/micropython.cmake" \
        FROZEN_MANIFEST="$PROJECT_ROOT/manifest.py" \
        CMAKE_ARGS="-DPICO_PIO_USB_PATH=$PIO_USB_DIR" \
        DEBUG=0
    
    if [ ! -f "build-$BOARD/firmware.uf2" ]; then
        log_error "Błąd kompilacji: firmware.uf2 nie znaleziony"
        return 1
    fi
    
    mkdir -p "$OUTPUT_DIR"
    cp "build-$BOARD/firmware.uf2" "$OUTPUT_DIR/firmware_rp2350_usb.uf2"
    cp "build-$BOARD/firmware.elf" "$OUTPUT_DIR/firmware_rp2350_usb.elf" || true
    
    log_info "✓ Firmware skompilowany: $OUTPUT_DIR/firmware_rp2350_usb.uf2"
    
    # Informacje o rozmiarze
    local size=$(ls -lh "$OUTPUT_DIR/firmware_rp2350_usb.uf2" | awk '{print $5}')
    log_info "  Rozmiar: $size"
}

#==============================================================================
# STAGE 5: WGRANIE NA PICO
#==============================================================================

stage_flash() {
    log_step "STAGE 5: Wgranie firmware na Pico"
    
    if [ ! -f "$OUTPUT_DIR/firmware_rp2350_usb.uf2" ]; then
        log_error "Firmware nie znaleziony: $OUTPUT_DIR/firmware_rp2350_usb.uf2"
        return 1
    fi
    
    log_warn "Przygotowanie do wgrania firmware"
    log_warn "1. Podłącz Pico przez USB"
    log_warn "2. Naciśnij BOOTSEL (przytrzymaj) i zaraz po podłączeniu zwolnij"
    log_warn "3. Pico powinno się zmontować jako dysk"
    log_warn ""
    read -p "Naciśnij Enter gdy będzie gotowe..."
    
    # Wyszukaj punkt montowania
    local mount_point=""
    for path in /media/$USER/RPI-RP2 /mnt/pico /mnt/pico2 /Volumes/RPI-RP2; do
        if [ -d "$path" ]; then
            mount_point="$path"
            break
        fi
    done
    
    # Spróbuj znaleźć poprzez lsblk
    if [ -z "$mount_point" ]; then
        log_info "Szukanie Pico..."
        mount_point=$(lsblk -o NAME,LABEL | grep -i "RPI-RP2\|PICO" | awk '{print "/media/$USER/"$2}' | head -n1)
    fi
    
    if [ -z "$mount_point" ]; then
        log_error "Nie znaleziono Pico. Czy jest podłączone w trybie BOOTSEL?"
        return 1
    fi
    
    if [ ! -d "$mount_point" ]; then
        log_error "Punkt montowania nie istnieje: $mount_point"
        return 1
    fi
    
    log_info "Wgrywanie do $mount_point..."
    cp "$OUTPUT_DIR/firmware_rp2350_usb.uf2" "$mount_point/"
    
    # Czekaj na odmontowanie (Pico restartuje się automatycznie)
    sleep 2
    log_info "✓ Firmware wgrany!"
    log_info "Pico powinno się teraz restartować..."
}

#==============================================================================
# STAGE 6: CZYSZCZENIE
#==============================================================================

stage_clean() {
    log_step "STAGE 6: Czyszczenie"
    
    log_info "Usuwanie plików buildu..."
    rm -rf "$BUILD_DIR"
    cd "$SOURCES_DIR/micropython/ports/rp2" && make clean BOARD="$BOARD" > /dev/null 2>&1 || true
    
    log_info "✓ Wyczyszczono"
}

#==============================================================================
# STAGE: ALL
#==============================================================================

stage_all() {
    log_step "KOMPILACJA PEŁNA (ALL)"
    stage_deps && \
    stage_sources && \
    stage_configure && \
    stage_build && \
    log_info "✓✓✓ FIRMWARE GOTOWY: $OUTPUT_DIR/firmware_rp2350_usb.uf2"
}

#==============================================================================
# GŁÓWNY PROGRAM
#==============================================================================

show_usage() {
    cat << EOF
Użycie: $0 [ETAP]

Dostępne etapy:
  all        - Wykonaj wszystkie etapy (domyślnie)
  deps       - Instaluj zależności (tylko raz)
  sources    - Pobierz źródła z GitHub
  configure  - Konfiguruj toolchain i Pico SDK
  build      - Skompiluj firmware
  flash      - Wgraj na Pico (wymaga BOOTSEL)
  clean      - Wyczyść pliki tymczasowe

Przykłady:
  $0              # Pełna kompilacja
  $0 build        # Tylko kompilacja (źródła już pobrane)
  $0 flash        # Wgraj na Pico

EOF
}

main() {
    local stage="${1:-all}"
    
    case "$stage" in
        all|deps|sources|configure|build|flash|clean)
            log_info "Raspberry Pi Pico 2 (RP2350) + MicroPython + USB CDC"
            log_info "Projekt: $PROJECT_ROOT"
            stage_$stage
            ;;
        help|-h|--help)
            show_usage
            ;;
        *)
            log_error "Nieznany etap: $stage"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
