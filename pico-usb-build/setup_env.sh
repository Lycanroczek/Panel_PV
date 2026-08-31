#!/bin/bash
#==============================================================================
# Arch Linux environment setup for Pico 2 USB project
# Skrypt automatycznego konfigurowania środowiska
#==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Pico 2 USB Project - Arch Linux Environment Setup     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

# Function to check if command exists
cmd_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install package
install_package() {
    local package=$1
    local cmd=${2:-$package}
    
    if cmd_exists "$cmd"; then
        echo -e "${GREEN}✓${NC} $package już zainstalowany"
        return 0
    fi
    
    echo -e "${YELLOW}→${NC} Instalowanie $package..."
    if sudo pacman -S --noconfirm "$package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $package zainstalowany"
        return 0
    else
        echo -e "${RED}✗${NC} Nie udało się zainstalować $package"
        return 1
    fi
}

# Step 1: Check Arch Linux
echo -e "${BLUE}[1/5]${NC} Sprawdzanie systemu..."
if [ ! -f /etc/arch-release ]; then
    echo -e "${YELLOW}⚠${NC}  Nie wygląda na Arch Linuxa (ale mogę spróbować)"
fi

# Step 2: Check and install basic tools
echo -e "\n${BLUE}[2/5]${NC} Sprawdzanie narzędzi..."

required_tools=(
    "git:git"
    "cmake:cmake"
    "python3:python3"
    "gcc:gcc"
    "make:make"
    "pkg-config:pkg-config"
)

for tool_pair in "${required_tools[@]}"; do
    IFS=':' read -r package cmd <<<"$tool_pair"
    install_package "$package" "$cmd" || true
done

# Step 3: Check and install ARM toolchain
echo -e "\n${BLUE}[3/5]${NC} Sprawdzanie ARM toolchain..."

arm_tools=(
    "arm-none-eabi-gcc:arm-none-eabi-gcc"
    "arm-none-eabi-gdb:arm-none-eabi-gdb"
    "arm-none-eabi-binutils:arm-none-eabi-ar"
    "arm-none-eabi-newlib:arm-none-eabi-ar"
)

for tool_pair in "${arm_tools[@]}"; do
    IFS=':' read -r package cmd <<<"$tool_pair"
    install_package "$package" "$cmd" || true
done

# Step 4: Install optional but useful tools
echo -e "\n${BLUE}[4/5]${NC} Instalowanie narzędzi opcjonalnych..."

optional_tools=(
    "openocd:openocd"
    "minicom:minicom"
    "picocom:picocom"
)

for tool_pair in "${optional_tools[@]}"; do
    IFS=':' read -r package cmd <<<"$tool_pair"
    if ! cmd_exists "$cmd"; then
        echo -e "${YELLOW}→${NC} Instalowanie $package (opcjonalnie)..."
        sudo pacman -S --noconfirm "$package" 2>/dev/null || echo -e "${YELLOW}⚠${NC}  Pominięto $package"
    else
        echo -e "${GREEN}✓${NC} $package już zainstalowany"
    fi
done

# Step 5: Create environment variables
echo -e "\n${BLUE}[5/5]${NC} Konfigurowanie zmiennych środowiskowych..."

# Create .env file
cat > "$PROJECT_ROOT/.env.local" << 'EOF'
#!/bin/bash
# Environment variables for Pico USB project
# Source this file: source .env.local

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PICO_SDK_PATH="$PROJECT_ROOT/sources/pico-sdk"
export PICO_TINYUSB_PATH="$PROJECT_ROOT/sources/tinyusb"
export MICROPYTHON_DIR="$PROJECT_ROOT/sources/micropython"
export PICOTOOL_ALLOW_UNSAFE_LIBUSB=1

# ARM toolchain paths (usually auto-detected, but can be overridden)
export ARM_GCC_TOOLCHAIN=$(arm-none-eabi-gcc --print-file-name=)
export CMAKE_C_COMPILER=$(which arm-none-eabi-gcc)
export CMAKE_CXX_COMPILER=$(which arm-none-eabi-g++)

# Build directories
export BUILD_DIR="$PROJECT_ROOT/build"
export FIRMWARE_DIR="$PROJECT_ROOT/firmware"

echo "[✓] Environment variables loaded"
EOF

chmod +x "$PROJECT_ROOT/.env.local"

echo -e "${GREEN}✓${NC} Plik .env.local utworzony"

# Create shell alias helper
cat > "$PROJECT_ROOT/load-env.sh" << 'EOF'
#!/bin/bash
# Helper to load environment
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_ROOT/.env.local"
EOF

chmod +x "$PROJECT_ROOT/load-env.sh"

# Verify installations
echo -e "\n${BLUE}═════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Weryfikacja instalacji:${NC}\n"

# Check each tool
tools_to_check=(
    "git:GIT"
    "cmake:CMAKE"
    "python3:PYTHON"
    "gcc:GCC"
    "arm-none-eabi-gcc:ARM-GCC"
    "make:MAKE"
)

all_ok=true
for tool_pair in "${tools_to_check[@]}"; do
    IFS=':' read -r cmd name <<<"$tool_pair"
    if cmd_exists "$cmd"; then
        version=$($cmd --version 2>/dev/null | head -1 | cut -d' ' -f3,4,5)
        printf "  ${GREEN}✓${NC} %-20s %s\n" "$name:" "$version"
    else
        printf "  ${RED}✗${NC} %-20s NOT FOUND\n" "$name:"
        all_ok=false
    fi
done

echo -e "\n${BLUE}═════════════════════════════════════════════════════${NC}"

# Summary
if [ "$all_ok" = true ]; then
    echo -e "\n${GREEN}✓✓✓ Wszystko gotowe!${NC}\n"
    echo -e "Kolejne kroki:\n"
    echo -e "  1. Załaduj zmienne: ${YELLOW}source .env.local${NC}"
    echo -e "  2. Pobierz źródła:  ${YELLOW}./build.sh sources${NC}"
    echo -e "  3. Skompiluj:       ${YELLOW}./build.sh build${NC}"
    echo -e "  4. Wgraj:           ${YELLOW}./build.sh flash${NC}"
    echo -e "\nAlbo wszystko naraz: ${YELLOW}./build.sh all${NC}"
else
    echo -e "\n${YELLOW}⚠${NC}  Niektóre narzędzia nie zostały zainstalowane."
    echo -e "Spróbuj zainstalować je ręcznie lub postępuj zgodnie z README.md\n"
fi

# Offer to load environment immediately
read -p "Załadować zmienne teraz? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    source "$PROJECT_ROOT/.env.local"
    echo -e "${GREEN}✓${NC} Zmienne załadowane w bieżącej sesji"
fi
