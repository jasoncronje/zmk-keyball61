/*
 * Left half (peripheral): tracks its battery, its link to the right half, the
 * right half's layer and Touch ID for layout_peripheral(), and redraws through
 * the Touch ID countdown.
 */

#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/spinlock.h>

#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/split_peripheral_status_changed.h>
#include <zmk/split/bluetooth/peripheral.h>

#include "layout.h"
#include "status_screen.h"

#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_POWER)
#define OFF_DELAY_MS (CONFIG_KEYBALL61_TOUCHID_OFF_DELAY_SEC * 1000U)
// LAYOUT_TOUCHID_STEPS redraws through the countdown
#define BAR_STEP K_MSEC(OFF_DELAY_MS / LAYOUT_TOUCHID_STEPS)

static void touchid_redraw_work_cb(struct k_work *work);

static K_WORK_DELAYABLE_DEFINE(touchid_redraw_work, touchid_redraw_work_cb);

static void touchid_redraw_work_cb(struct k_work *work) {
    status_screen_redraw();

    // Keep redrawing while the countdown runs
    if (keyball61_touchid_off_remaining_ms() > 0) {
        k_work_reschedule_for_queue(zmk_display_work_q(), &touchid_redraw_work, BAR_STEP);
    }
}

void keyball61_touchid_display_update(void) {
    k_work_reschedule_for_queue(zmk_display_work_q(), &touchid_redraw_work, K_NO_WAIT);
}
#endif

// The right half's layer name, from layer_sync.c on the split link's thread
static struct k_spinlock layer_lock;
static char layer_name[9];
static bool layer_known;

void status_screen_set_layer_name(const char *name) {
    K_SPINLOCK(&layer_lock) {
        strncpy(layer_name, name, sizeof(layer_name) - 1);
        layer_known = true;
    }
    status_screen_redraw();
}

void status_screen_draw(void) {
    char layer[sizeof(layer_name)];
    bool known;
    K_SPINLOCK(&layer_lock) {
        strcpy(layer, layer_name);
        known = layer_known;
    }

    struct peripheral_status status = {
        .layer_name = known ? layer : NULL,
        .battery = status_screen_battery_level(),
        .charging = status_screen_charging(),
        .linked = zmk_split_bt_peripheral_is_connected(),
    };

#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_POWER)
    status.touchid = true;
    status.touchid_mode = keyball61_touchid_mode();
    status.touchid_on = keyball61_touchid_is_on();
    status.touchid_remaining_ms = keyball61_touchid_off_remaining_ms();
    status.touchid_off_delay_ms = OFF_DELAY_MS;
#endif

    layout_peripheral(&status);
}

static int link_listener_cb(const zmk_event_t *eh) {
    status_screen_redraw();
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(status_screen_link, link_listener_cb);
ZMK_SUBSCRIPTION(status_screen_link, zmk_split_peripheral_status_changed);
