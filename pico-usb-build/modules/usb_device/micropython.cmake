# CMake configuration for USB CDC device module
# Automatically included by MicroPython build system via USER_C_MODULES

add_library(usermod_usb_device INTERFACE)

target_sources(usermod_usb_device INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/usb_module.c
)

target_include_directories(usermod_usb_device INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

# Link against TinyUSB (już dostępny z Pico SDK)
target_link_libraries(usermod_usb_device INTERFACE
    tinyusb_common
    tinyusb_device
    pico_stdlib
)

# Ensure TinyUSB is built with CDC support
target_compile_definitions(usermod_usb_device INTERFACE
    CFG_TUD_CDC=1
    CFG_TUD_CDC_RX_BUFSIZE=256
    CFG_TUD_CDC_TX_BUFSIZE=256
)

# Register with MicroPython
target_link_libraries(usermod INTERFACE usermod_usb_device)
