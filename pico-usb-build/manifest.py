# MicroPython Manifest - frozen modules
# Definiuje, które pliki Python będą zamrożone w firmware

include("$(PORT_DIR)/boards/manifest.py")

# Dodaj USB device module
c_module("modules/usb_device")

# Dodaj przykładowe kody (opcjonalnie)
freeze("examples", "test_usb.py")
