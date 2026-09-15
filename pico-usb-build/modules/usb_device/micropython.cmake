# CMake configuration for USB CDC device module
# Automatically included by MicroPython build system via USER_C_MODULES

add_library(usermod_usb_device INTERFACE)

if(NOT PICO_PIO_USB_PATH OR NOT EXISTS "${PICO_PIO_USB_PATH}/src/pio_usb.c")
    message(FATAL_ERROR "PICO_PIO_USB_PATH must point to Pico-PIO-USB")
endif()

target_sources(usermod_usb_device INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/usb_module.c
    ${CMAKE_CURRENT_LIST_DIR}/usb_pio_tinyusb_bridge.c
    ${PICO_PIO_USB_PATH}/src/pio_usb.c
    ${PICO_PIO_USB_PATH}/src/pio_usb_device.c
    ${PICO_PIO_USB_PATH}/src/usb_crc.c
)

target_include_directories(usermod_usb_device INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${PICO_PIO_USB_PATH}/src
)

pico_generate_pio_header(usermod_usb_device ${PICO_PIO_USB_PATH}/src/usb_tx.pio)
pico_generate_pio_header(usermod_usb_device ${PICO_PIO_USB_PATH}/src/usb_rx.pio)

target_link_libraries(usermod_usb_device INTERFACE
    tinyusb_common
    tinyusb_device
    hardware_dma
    hardware_pio
    hardware_irq
    hardware_clocks
    pico_stdlib
    pico_multicore
)

# Ensure TinyUSB is built with CDC support
target_compile_definitions(usermod_usb_device INTERFACE
    CFG_TUSB_MCU=OPT_MCU_RP2040
    CFG_TUD_ENABLED=1
    CFG_TUD_RPI_PIO_USB=1
    TUD_OPT_RHPORT=1
    CFG_TUSB_RHPORT1_MODE=OPT_MODE_DEVICE
    CFG_TUSB_RHPORT0_MODE=OPT_MODE_NONE
    CFG_TUD_CDC=1
    PIO_USB_USE_TINYUSB=1
    PIO_USB_DP_PIN_DEFAULT=10
    CFG_TUD_CDC_RX_BUFSIZE=256
    CFG_TUD_CDC_TX_BUFSIZE=256
)

# Register with MicroPython
target_link_libraries(usermod INTERFACE usermod_usb_device)
