# Custom board based on RPI_PICO2.
set(PICO_BOARD "pico2")
set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)

# PIO-USB derives D- from D+ + 1.  GPIO10 therefore means D+=10, D-=11.
set(PIO_USB_DP_PIN_DEFAULT 10)

# Do not initialise the RP2350's native USB controller.  The C module owns the
# external PIO USB controller instead.
set(MICROPY_HW_ENABLE_USBDEV 0)
set(MICROPY_HW_ENABLE_UART_REPL 1)

if(NOT DEFINED MICROPY_HW_FLASH_STORAGE_BYTES)
	set(MICROPY_HW_FLASH_STORAGE_BYTES 3145728)
endif()
