#include "usb_pio_tinyusb_bridge.h"

#include "tusb.h"
#include "device/dcd.h"
#include "device/usbd.h"
#include "class/cdc/cdc_device.h"
#include "pio_usb.h"
#include "pio_usb_ll.h"
#include "hardware/clocks.h"
#include <string.h>

#define PIO_USB_RHPORT 1
#define PIO_USB_DP_PIN 10
#define CDC_ITF_CONTROL 0
#define CDC_ITF_DATA 1
#define CDC_EP_NOTIFICATION 0x81
#define CDC_EP_OUT 0x02
#define CDC_EP_IN 0x82
#define CDC_CONFIG_LEN (TUD_CONFIG_DESC_LEN + TUD_CDC_DESC_LEN)

static volatile bool bridge_mounted;
static volatile bool bridge_connected;
static bool bridge_initialized;
static usb_descriptor_buffers_t pio_descriptors;
static string_descriptor_t pio_strings[4];
static tusb_desc_device_t const device_descriptor = {
    .bLength = sizeof(tusb_desc_device_t),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,
    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,
    .idVendor = 0xCafe,
    .idProduct = 0x4010,
    .bcdDevice = 0x0100,
    .iManufacturer = 1,
    .iProduct = 2,
    .iSerialNumber = 3,
    .bNumConfigurations = 1,
};
static uint8_t const configuration_descriptor[] = {
    TUD_CONFIG_DESCRIPTOR(1, 2, 0, CDC_CONFIG_LEN, 0, 100),
    TUD_CDC_DESCRIPTOR(CDC_ITF_CONTROL, 4, CDC_EP_NOTIFICATION, 8,
                       CDC_EP_OUT, CDC_EP_IN, 64),
};

static void init_pio_strings(void) {
    static char const *const text[] = {NULL, "Pico PIO USB", "RP2350 CDC", "PIO10-11"};
    for (size_t index = 0; index < 4; ++index) {
        uint16_t *out = (uint16_t *)&pio_strings[index];
        size_t length = index == 0 ? 1 : strlen(text[index]);
        if (length > 31) length = 31;
        if (index == 0) out[1] = 0x0409;
        for (size_t i = index == 0 ? 1 : 0; i < length; ++i) out[i + 1] = (uint8_t)text[index][i];
        out[0] = (uint16_t)((TUSB_DESC_STRING << 8) | (2 * length + 2));
    }
    pio_descriptors.device = (uint8_t const *)&device_descriptor;
    pio_descriptors.config = configuration_descriptor;
    pio_descriptors.hid_report = NULL;
    pio_descriptors.string = pio_strings;
}

uint8_t const *tud_descriptor_device_cb(void) { return (uint8_t const *)&device_descriptor; }
uint8_t const *tud_descriptor_configuration_cb(uint8_t index) {
    (void)index;
    return configuration_descriptor;
}
uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t langid) {
    (void)langid;
    return index < 4 ? (uint16_t const *)&pio_strings[index] : NULL;
}

bool dcd_init(uint8_t rhport, tusb_rhport_init_t const *rh_init) {
    (void)rhport;
    (void)rh_init;
    static pio_usb_configuration_t config = PIO_USB_DEFAULT_CONFIG;
    config.pin_dp = PIO_USB_DP_PIN;
    config.pinout = PIO_USB_PINOUT_DPDM;
    pio_usb_device_init(&config, &pio_descriptors);
    return true;
}
void dcd_int_enable(uint8_t rhport) { (void)rhport; }
void dcd_int_disable(uint8_t rhport) { (void)rhport; }
void dcd_int_handler(uint8_t rhport) { (void)rhport; }
void dcd_sof_enable(uint8_t rhport, bool enable) { (void)rhport; (void)enable; }
void dcd_set_address(uint8_t rhport, uint8_t address) {
    pio_usb_device_set_address(address);
    dcd_edpt_xfer(rhport, 0x80, NULL, 0, false);
}
void dcd_remote_wakeup(uint8_t rhport) { (void)rhport; }
void dcd_connect(uint8_t rhport) { (void)rhport; }
void dcd_disconnect(uint8_t rhport) { (void)rhport; }
bool dcd_configure(uint8_t rhport, uint32_t cfg_id, void const *cfg_param) {
    (void)rhport; (void)cfg_id; (void)cfg_param; return false;
}
bool dcd_deinit(uint8_t rhport) { (void)rhport; return true; }
void dcd_edpt0_status_complete(uint8_t rhport, tusb_control_request_t const *request) {
    (void)rhport; (void)request;
}
bool dcd_edpt_open(uint8_t rhport, tusb_desc_endpoint_t const *desc_ep) {
    (void)rhport;
    return pio_usb_device_endpoint_open((uint8_t const *)desc_ep);
}
void dcd_edpt_close_all(uint8_t rhport) { (void)rhport; }
bool dcd_edpt_xfer(uint8_t rhport, uint8_t ep_addr, uint8_t *buffer,
                   uint16_t total_bytes, bool is_isr) {
    (void)rhport; (void)is_isr;
    endpoint_t *endpoint = pio_usb_device_get_endpoint_by_address(ep_addr);
    return endpoint != NULL && pio_usb_ll_transfer_start(endpoint, buffer, total_bytes);
}
void dcd_edpt_stall(uint8_t rhport, uint8_t ep_addr) {
    (void)rhport;
    endpoint_t *endpoint = pio_usb_device_get_endpoint_by_address(ep_addr);
    if (endpoint != NULL) { endpoint->has_transfer = false; endpoint->stalled = true; }
}
void dcd_edpt_clear_stall(uint8_t rhport, uint8_t ep_addr) {
    (void)rhport;
    endpoint_t *endpoint = pio_usb_device_get_endpoint_by_address(ep_addr);
    if (endpoint != NULL) { endpoint->data_id = 0; endpoint->stalled = false; }
}
void pio_usb_tinyusb_reset(void) {
    dcd_event_bus_reset(PIO_USB_RHPORT, TUSB_SPEED_FULL, true);
}
void pio_usb_tinyusb_setup_received(uint8_t const *setup) {
    dcd_event_setup_received(PIO_USB_RHPORT, setup, true);
}
void pio_usb_tinyusb_transfer_complete(uint8_t ep_addr, uint16_t length, uint8_t result) {
    dcd_event_xfer_complete(PIO_USB_RHPORT, ep_addr, length, result, true);
}

bool usb_pio_tinyusb_init(void) {
    if (bridge_initialized) return true;
    set_sys_clock_khz(120000, true);
    init_pio_strings();
    tusb_rhport_init_t init = {
        .role = TUSB_ROLE_DEVICE,
        .speed = TUSB_SPEED_FULL,
    };
    if (!tusb_rhport_init(PIO_USB_RHPORT, &init)) return false;
    bridge_initialized = true;
    return true;
}
void usb_pio_tinyusb_task(void) {
    if (!bridge_initialized) return;
    pio_usb_device_task();
    tud_task_ext(0, false);
}
void usb_pio_tinyusb_deinit(void) {
    if (bridge_initialized) tud_deinit(PIO_USB_RHPORT);
    bridge_initialized = false;
    bridge_mounted = false;
    bridge_connected = false;
}
bool usb_pio_tinyusb_mounted(void) { return bridge_mounted; }
bool usb_pio_tinyusb_connected(void) { return bridge_connected; }
void tud_mount_cb(void) { bridge_mounted = true; bridge_connected = true; }
void tud_umount_cb(void) { bridge_mounted = false; bridge_connected = false; }
void tud_suspend_cb(bool remote_wakeup_en) { (void)remote_wakeup_en; bridge_connected = false; }
void tud_resume_cb(void) { bridge_connected = true; }
