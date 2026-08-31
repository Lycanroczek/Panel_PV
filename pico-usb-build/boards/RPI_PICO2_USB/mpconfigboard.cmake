# Raspberry Pi Pico 2 (RP2350) with USB CDC on GPIO10/GPIO11
# MicroPython Board Configuration

# Zmienne definiujące platform i board
set(PICO_PLATFORM rp2350)
set(PICO_BOARD pico2)

# USB via GPIO10/GPIO11 (PIO-USB)
set(PICO_DEFAULT_PIO_USB_DP_PIN 10)   # USB D+ on GPIO 10
set(PICO_DEFAULT_PIO_USB_DM_PIN 11)   # USB D- on GPIO 11

# VBUS (opcjonalnie - dla zasilania USB z Pico)
set(PICO_DEFAULT_PIO_USB_VBUSEN_PIN 12)
set(PICO_DEFAULT_PIO_USB_VBUSEN_STATE 1)

# TinyUSB konfiguracja - enable PIO-USB w Device mode
set(CFG_TUD_RPI_PIO_USB 1)
set(CFG_TUD_CDC 1)

# System Clock - RP2350 @ 150 MHz (dla stabilności PIO-USB)
# TinyUSB zaleca 150 MHz dla RP2350 z PIO-USB
set(PICO_DEFAULT_FREQ_KHZ 150000)

# Zwiększ stack dla MicroPython
set(PICO_HEAP_SIZE 0x30000)  # 192 KB

# USB REPL
set(MICROPY_PY_USDBVCP 1)

# Wgraj jako USB Device
set(PICO_BUILD_USB_DEVICE 1)

# Disable PIO-USB Host mode (chcemy tylko Device)
set(CFG_TUH_RPI_PIO_USB 0)
set(CFG_TUH_ENABLED 0)
