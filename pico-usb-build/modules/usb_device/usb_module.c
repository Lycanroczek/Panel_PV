/*
 * Raspberry Pi Pico 2 - USB CDC Device Module for MicroPython
 * Obsługuje USB CDC (virtual serial port) na GPIO10/GPIO11 via PIO-USB
 * 
 * Interfejs Python:
 *   import usb_device
 *   usb_device.init()
 *   if usb_device.is_ready():
 *       data = usb_device.read(n)
 *   usb_device.write(b"hello")
 */

#include "py/builtin.h"
#include "py/obj.h"
#include "py/objstr.h"
#include "py/runtime.h"
#include "py/stream.h"

#include "tusb.h"
#include "bsp/board.h"

#include <string.h>
#include <stdio.h>

/*=====================================================================
  CONFIGURATION
 =====================================================================*/

#define USB_BUFFER_SIZE 256
#define TASK_INTERVAL_US 1000

/*=====================================================================
  RINGBUFFER - dla bezpiecznego bufferowania danych
 =====================================================================*/

typedef struct {
    uint8_t buffer[USB_BUFFER_SIZE];
    uint16_t head;
    uint16_t tail;
    uint16_t count;
} ringbuffer_t;

static ringbuffer_t rx_buffer = {0};
static ringbuffer_t tx_buffer = {0};
static volatile bool usb_initialized = false;
static volatile bool usb_connected = false;
static volatile bool usb_mounted = false;

static inline void rb_init(ringbuffer_t *rb) {
    rb->head = 0;
    rb->tail = 0;
    rb->count = 0;
}

static inline bool rb_write(ringbuffer_t *rb, uint8_t data) {
    if (rb->count >= USB_BUFFER_SIZE) {
        return false; // Buffer full
    }
    rb->buffer[rb->head] = data;
    rb->head = (rb->head + 1) % USB_BUFFER_SIZE;
    rb->count++;
    return true;
}

static inline bool rb_read(ringbuffer_t *rb, uint8_t *data) {
    if (rb->count == 0) {
        return false; // Buffer empty
    }
    *data = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) % USB_BUFFER_SIZE;
    rb->count--;
    return true;
}

static inline uint16_t rb_count(ringbuffer_t *rb) {
    return rb->count;
}

static inline void rb_clear(ringbuffer_t *rb) {
    rb->head = 0;
    rb->tail = 0;
    rb->count = 0;
}

/*=====================================================================
  TINYUSB CALLBACKS
 =====================================================================*/

// Callback gdy USB device zostanie zmountowane
void tud_mount_cb(void) {
    usb_mounted = true;
    usb_connected = true;
}

// Callback gdy USB device zostanie odmountowane
void tud_umount_cb(void) {
    usb_mounted = false;
    usb_connected = false;
}

// Callback gdy USB suspend
void tud_suspend_cb(bool remote_wakeup_en) {
    (void)remote_wakeup_en;
    usb_connected = false;
}

// Callback gdy USB resume
void tud_resume_cb(void) {
    usb_connected = true;
}

// CDC Data Receive Callback
void tud_cdc_rx_cb(uint8_t itf) {
    (void)itf;
    
    // Przeczytaj dostępne dane z CDC
    while (tud_cdc_available()) {
        uint8_t data = tud_cdc_read_char();
        rb_write(&rx_buffer, data);
    }
}

/*=====================================================================
  SYSTEM TASK (do wywoływania z MicroPython main loop)
 =====================================================================*/

static void usb_task(void) {
    if (!usb_initialized) return;
    
    // TinyUSB task
    tud_task();
    
    // Jeśli jest dane w TX buffer, wyślij
    if (usb_connected && rb_count(&tx_buffer) > 0) {
        uint8_t buf[64];
        uint8_t len = 0;
        
        while (len < 64 && rb_read(&tx_buffer, &buf[len])) {
            len++;
        }
        
        if (len > 0 && tud_cdc_connected()) {
            tud_cdc_write(buf, len);
            tud_cdc_write_flush();
        }
    }
}

/*=====================================================================
  MICROPYTHON MODULE METHODS
 =====================================================================*/

// usb_device.init()
static mp_obj_t usb_init(void) {
    if (usb_initialized) {
        return mp_const_none;
    }
    
    // Inicjalizuj TinyUSB
    tusb_init();
    
    usb_initialized = true;
    rb_init(&rx_buffer);
    rb_init(&tx_buffer);
    
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_init_obj, usb_init);

// usb_device.is_ready()
static mp_obj_t usb_is_ready(void) {
    usb_task();
    return mp_obj_new_bool(usb_mounted && tud_cdc_connected());
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_is_ready_obj, usb_is_ready);

// usb_device.is_connected()
static mp_obj_t usb_is_connected(void) {
    usb_task();
    return mp_obj_new_bool(usb_connected);
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_is_connected_obj, usb_is_connected);

// usb_device.any() - czy są dostępne dane?
static mp_obj_t usb_any(void) {
    usb_task();
    return mp_obj_new_int(rb_count(&rx_buffer));
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_any_obj, usb_any);

// usb_device.read(n) - czytaj do n bajtów
static mp_obj_t usb_read(size_t n_args, const mp_obj_t *args) {
    usb_task();
    
    int n = USB_BUFFER_SIZE;
    if (n_args > 1) {
        n = mp_obj_get_int(args[1]);
    }
    if (n > USB_BUFFER_SIZE) {
        n = USB_BUFFER_SIZE;
    }
    
    uint8_t buf[n];
    int len = 0;
    
    while (len < n && rb_read(&rx_buffer, &buf[len])) {
        len++;
    }
    
    return mp_obj_new_bytes(buf, len);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(usb_read_obj, 1, 2, usb_read);

// usb_device.read_line() - czytaj do \n
static mp_obj_t usb_read_line(void) {
    usb_task();
    
    uint8_t buf[USB_BUFFER_SIZE];
    int len = 0;
    uint8_t data;
    
    while (rb_read(&rx_buffer, &data) && len < USB_BUFFER_SIZE) {
        buf[len++] = data;
        if (data == '\n') {
            break;
        }
    }
    
    return mp_obj_new_bytes(buf, len);
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_read_line_obj, usb_read_line);

// usb_device.write(data)
static mp_obj_t usb_write(mp_obj_t data_obj) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(data_obj, &bufinfo, MP_BUFFER_READ);
    
    usb_task();
    
    int written = 0;
    for (int i = 0; i < bufinfo.len; i++) {
        if (rb_write(&tx_buffer, ((uint8_t*)bufinfo.buf)[i])) {
            written++;
        } else {
            break; // Buffer full
        }
    }
    
    // Trigger send
    usb_task();
    
    return mp_obj_new_int(written);
}
static MP_DEFINE_CONST_FUN_OBJ_1(usb_write_obj, usb_write);

// usb_device.write_str(string)
static mp_obj_t usb_write_str(mp_obj_t data_obj) {
    const char *str = mp_obj_str_get_str(data_obj);
    size_t len = strlen(str);
    
    usb_task();
    
    int written = 0;
    for (size_t i = 0; i < len; i++) {
        if (rb_write(&tx_buffer, (uint8_t)str[i])) {
            written++;
        } else {
            break;
        }
    }
    
    usb_task();
    return mp_obj_new_int(written);
}
static MP_DEFINE_CONST_FUN_OBJ_1(usb_write_str_obj, usb_write_str);

// usb_device.flush()
static mp_obj_t usb_flush(void) {
    usb_task();
    int timeout = 100;
    while (rb_count(&tx_buffer) > 0 && timeout-- > 0) {
        usb_task();
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_flush_obj, usb_flush);

// usb_device.deinit()
static mp_obj_t usb_deinit(void) {
    usb_initialized = false;
    usb_connected = false;
    usb_mounted = false;
    rb_clear(&rx_buffer);
    rb_clear(&tx_buffer);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(usb_deinit_obj, usb_deinit);

/*=====================================================================
  MODULE DEFINITION
 =====================================================================*/

static const mp_rom_map_elem_t usb_device_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_usb_device) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&usb_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_is_ready), MP_ROM_PTR(&usb_is_ready_obj) },
    { MP_ROM_QSTR(MP_QSTR_is_connected), MP_ROM_PTR(&usb_is_connected_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&usb_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&usb_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_read_line), MP_ROM_PTR(&usb_read_line_obj) },
    { MP_ROM_QSTR(MP_QSTR_write), MP_ROM_PTR(&usb_write_obj) },
    { MP_ROM_QSTR(MP_QSTR_write_str), MP_ROM_PTR(&usb_write_str_obj) },
    { MP_ROM_QSTR(MP_QSTR_flush), MP_ROM_PTR(&usb_flush_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&usb_deinit_obj) },
};
static MP_DEFINE_CONST_DICT(usb_device_module_globals, usb_device_module_globals_table);

const mp_obj_module_t usb_device_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&usb_device_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_usb_device, usb_device_module);
