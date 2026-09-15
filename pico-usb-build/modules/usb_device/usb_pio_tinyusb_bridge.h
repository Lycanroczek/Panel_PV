#pragma once

#include <stdbool.h>
#include <stdint.h>

bool usb_pio_tinyusb_init(void);
void usb_pio_tinyusb_task(void);
void usb_pio_tinyusb_deinit(void);
bool usb_pio_tinyusb_mounted(void);
bool usb_pio_tinyusb_connected(void);
