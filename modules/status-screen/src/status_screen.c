/*
 * Status screen for the Keyball61 OLEDs, replacing zmk-nice-oled's widgets.
 * Each half draws a portrait 32x128 frame (draw.h) in labelled blocks; this file
 * owns the LVGL canvas, turns the frame into the landscape 128x32 panel and
 * tracks this half's battery, which both halves show.
 */

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>

#include <lvgl.h>

#include <zmk/battery.h>
#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/usb.h>

#include "draw.h"
#include "status_screen.h"

// The panel is landscape; the screen is read with the panel's right end at the top
#define PANEL_W SCREEN_H
#define PANEL_H SCREEN_W

// The panel's overlay sets inversion-on, so a white canvas pixel shows dark
#define COLOR_LIT lv_color_black()
#define COLOR_DARK lv_color_white()

static lv_obj_t *canvas;
static lv_color_t canvas_buf[PANEL_W * PANEL_H];

static uint8_t battery_level;

uint8_t status_screen_battery_level(void) { return battery_level; }

bool status_screen_charging(void) {
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    return zmk_usb_is_powered();
#else
    return false;
#endif
}

static void redraw_work_cb(struct k_work *work) {
    if (canvas == NULL) {
        return;
    }

    draw_clear();
    status_screen_draw();

    lv_img_dsc_t *img = lv_canvas_get_img(canvas);
    for (int y = 0; y < SCREEN_H; y++) {
        for (int x = 0; x < SCREEN_W; x++) {
            lv_img_buf_set_px_color(img, SCREEN_H - 1 - y, x,
                                    draw_get(x, y) ? COLOR_LIT : COLOR_DARK);
        }
    }
    lv_obj_invalidate(canvas);
}

static K_WORK_DEFINE(redraw_work, redraw_work_cb);

void status_screen_redraw(void) {
    if (zmk_display_is_initialized()) {
        k_work_submit_to_queue(zmk_display_work_q(), &redraw_work);
    }
}

#if IS_ENABLED(CONFIG_USB_DEVICE_STACK) && DT_HAS_CHOSEN(zmk_battery)
// Right after unplugging, the reading still includes the charger, and ZMK only
// samples again at its report interval, so read the battery once it has settled
#define UNPLUG_SETTLE_DELAY K_SECONDS(10)

static const struct device *const battery = DEVICE_DT_GET(DT_CHOSEN(zmk_battery));

static void unplug_settle_work_cb(struct k_work *work) {
    struct sensor_value state_of_charge;

    if (zmk_usb_is_powered() || !device_is_ready(battery) ||
        sensor_sample_fetch_chan(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE) < 0 ||
        sensor_channel_get(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE, &state_of_charge) < 0) {
        return;
    }

    battery_level = CLAMP(state_of_charge.val1, 0, 100);
    status_screen_redraw();
}

static K_WORK_DELAYABLE_DEFINE(unplug_settle_work, unplug_settle_work_cb);

static void usb_changed(void) {
    if (zmk_usb_is_powered()) {
        k_work_cancel_delayable(&unplug_settle_work);
    } else {
        k_work_reschedule(&unplug_settle_work, UNPLUG_SETTLE_DELAY);
    }
}
#else
static void usb_changed(void) {}
#endif

static int battery_listener_cb(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *ev = as_zmk_battery_state_changed(eh);
    if (ev != NULL) {
        battery_level = ev->state_of_charge;
    } else {
        usb_changed();
    }

    status_screen_redraw();
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(status_screen_battery, battery_listener_cb);
ZMK_SUBSCRIPTION(status_screen_battery, zmk_battery_state_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(status_screen_battery, zmk_usb_conn_state_changed);
#endif

// Called once by ZMK on the display work queue
lv_obj_t *zmk_display_status_screen(void) {
    lv_obj_t *screen = lv_obj_create(NULL);

    canvas = lv_canvas_create(screen);
    lv_obj_align(canvas, LV_ALIGN_TOP_LEFT, 0, 0);
    lv_canvas_set_buffer(canvas, canvas_buf, PANEL_W, PANEL_H, LV_IMG_CF_TRUE_COLOR);

    battery_level = zmk_battery_state_of_charge();
    redraw_work_cb(NULL);

    return screen;
}
