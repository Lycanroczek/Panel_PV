# Makefile snippet for USB CDC module
# Used by legacy MicroPython Makefile build (if applicable)

# Add C module source files
SRC_USERMOD += $(USERMOD_DIR)/usb_module.c

# Include directories
INC += -I$(USERMOD_DIR)

# C Compiler flags
CFLAGS_USERMOD += -std=c99

# TinyUSB configuration
CFLAGS_USERMOD += \
    -DCFG_TUD_CDC=1 \
    -DCFG_TUD_CDC_RX_BUFSIZE=256 \
    -DCFG_TUD_CDC_TX_BUFSIZE=256
