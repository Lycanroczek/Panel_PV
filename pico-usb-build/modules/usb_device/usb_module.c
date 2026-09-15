#include "py/runtime.h"
#include "py/mphal.h"
#include "hardware/sync.h"
#include "pico/multicore.h"
#include "class/cdc/cdc_device.h"
#include "usb_pio_tinyusb_bridge.h"

#include <string.h>

#define USB_BUFFER_SIZE 256

typedef struct {
    uint8_t data[USB_BUFFER_SIZE];
    volatile uint16_t put;
    volatile uint16_t get;
} usb_ring_t;

static usb_ring_t rx_ring;
static usb_ring_t tx_ring;
static volatile bool usb_initialised;
static volatile bool service_running;
static volatile bool service_started;

static inline uint16_t ring_next(uint16_t index) {
    return (uint16_t)((index + 1u) % USB_BUFFER_SIZE);
}

static bool ring_put(usb_ring_t *ring, uint8_t value) {
    uint16_t put = ring->put;
    uint16_t next = ring_next(put);
    if (next == ring->get) return false;
    ring->data[put] = value;
    __dmb();
    ring->put = next;
    return true;
}

static bool ring_get(usb_ring_t *ring, uint8_t *value) {
    uint16_t get = ring->get;
    if (get == ring->put) return false;
    *value = ring->data[get];
    __dmb();
    ring->get = ring_next(get);
    return true;
}

static size_t ring_count(const usb_ring_t *ring) {
    uint16_t put = ring->put;
    uint16_t get = ring->get;
    return put >= get ? put - get : USB_BUFFER_SIZE - get + put;
}

void tud_cdc_rx_cb(uint8_t itf) {
    (void)itf;
    uint8_t data[64];
    while (tud_cdc_available()) {
        uint32_t count = tud_cdc_read(data, sizeof(data));
        for (uint32_t i = 0; i < count; ++i) (void)ring_put(&rx_ring, data[i]);
    }
}

static void usb_service_core1(void) {
    while (true) {
        if (!service_running) {
            tight_loop_contents();
            continue;
        }
        usb_pio_tinyusb_task();
        if (tud_cdc_connected()) {
            uint8_t data[64];
            size_t count = ring_count(&tx_ring);
            if (count > sizeof(data)) count = sizeof(data);
            if (count > tud_cdc_write_available()) count = tud_cdc_write_available();
            for (size_t i = 0; i < count; ++i) (void)ring_get(&tx_ring, &data[i]);
            if (count != 0) {
                tud_cdc_write(data, count);
                tud_cdc_write_flush();
            }
        }
    }
}

static mp_obj_t usb_init(void) {
    if (!usb_initialised) {
        rx_ring.put = rx_ring.get = tx_ring.put = tx_ring.get = 0;
        if (!usb_pio_tinyusb_init()) mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("TinyUSB init failed"));
        service_running = true;
        if (!service_started) {
            service_started = true;
            multicore_launch_core1(usb_service_core1);
        }
        usb_initialised = true;
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_init_obj, usb_init);

static mp_obj_t usb_is_connected(void) {
    return mp_obj_new_bool(usb_initialised && usb_pio_tinyusb_connected());
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_is_connected_obj, usb_is_connected);

static mp_obj_t usb_is_ready(void) {
    return mp_obj_new_bool(usb_initialised && usb_pio_tinyusb_mounted() && tud_cdc_connected());
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_is_ready_obj, usb_is_ready);

static mp_obj_t usb_any(void) {
    return mp_obj_new_int_from_uint(ring_count(&rx_ring));
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_any_obj, usb_any);

static mp_obj_t usb_read(size_t n_args, const mp_obj_t *args) {
    mp_int_t requested = n_args == 1 ? USB_BUFFER_SIZE - 1 : mp_obj_get_int(args[1]);
    if (requested < 0) requested = 0;
    if (requested > USB_BUFFER_SIZE - 1) requested = USB_BUFFER_SIZE - 1;
    uint8_t data[USB_BUFFER_SIZE];
    size_t count = 0;
    while (count < (size_t)requested && ring_get(&rx_ring, &data[count])) ++count;
    return mp_obj_new_bytes(data, count);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(usb_read_obj, 1, 2, usb_read);

static mp_obj_t usb_write(mp_obj_t object) {
    mp_buffer_info_t buffer;
    mp_get_buffer_raise(object, &buffer, MP_BUFFER_READ);
    size_t count = 0;
    while (count < buffer.len && ring_put(&tx_ring, ((uint8_t *)buffer.buf)[count])) ++count;
    return mp_obj_new_int_from_uint(count);
}
static MP_DEFINE_CONST_FUN_OBJ_1(usb_write_obj, usb_write);

static mp_obj_t usb_write_str(mp_obj_t object) {
    const char *text = mp_obj_str_get_str(object);
    size_t length = strlen(text);
    size_t count = 0;
    while (count < length && ring_put(&tx_ring, (uint8_t)text[count])) ++count;
    return mp_obj_new_int_from_uint(count);
}
static MP_DEFINE_CONST_FUN_OBJ_1(usb_write_str_obj, usb_write_str);

static mp_obj_t usb_flush(void) {
    while (ring_count(&tx_ring) != 0) mp_hal_delay_ms(1);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_flush_obj, usb_flush);

static mp_obj_t usb_deinit(void) {
    service_running = false;
    usb_initialised = false;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_deinit_obj, usb_deinit);

static const mp_rom_map_elem_t usb_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_usb_device) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&usb_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_is_connected), MP_ROM_PTR(&usb_is_connected_obj) },
    { MP_ROM_QSTR(MP_QSTR_is_ready), MP_ROM_PTR(&usb_is_ready_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&usb_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&usb_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_write), MP_ROM_PTR(&usb_write_obj) },
    { MP_ROM_QSTR(MP_QSTR_write_str), MP_ROM_PTR(&usb_write_str_obj) },
    { MP_ROM_QSTR(MP_QSTR_flush), MP_ROM_PTR(&usb_flush_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&usb_deinit_obj) },
};
static MP_DEFINE_CONST_DICT(usb_module_globals, usb_module_globals_table);
const mp_obj_module_t usb_device_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&usb_module_globals,
};
MP_REGISTER_MODULE(MP_QSTR_usb_device, usb_device_module);
