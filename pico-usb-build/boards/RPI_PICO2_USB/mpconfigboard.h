// Raspberry Pi Pico 2 custom board.
// USB is deliberately disabled here: MicroPython's built-in USB is wired to
// the RP2350 USB peripheral, not to GPIO10/GPIO11.
#define MICROPY_HW_BOARD_NAME "Raspberry Pi Pico2 PIO USB"
#define MICROPY_HW_ENABLE_USBDEV (0)
#define MICROPY_HW_ENABLE_UART_REPL (1)
