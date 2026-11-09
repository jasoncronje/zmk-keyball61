/*
 * Right half (central): tracks both batteries, the output, the layer and the
 * held mods for layout_central().
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

#include <dt-bindings/zmk/hid_usage.h>
#include <dt-bindings/zmk/hid_usage_pages.h>
#include <dt-bindings/zmk/modifiers.h>

#include <zmk/ble.h>
#include <zmk/endpoints.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/keymap.h>

#include "layout.h"
#include "status_screen.h"

// Modifier keys held down, as MOD_* bits; tracked from key events rather than
// the HID report, which other listeners may not have updated yet
static atomic_t held_mods;

// The left half's battery; 0 until it first reports
static uint8_t peripheral_battery;

static uint8_t status_mods(void) {
    uint8_t held = atomic_get(&held_mods);
    uint8_t mods = 0;

    if (held & (MOD_LCTL | MOD_RCTL)) {
        mods |= STATUS_MOD_CTL;
    }
    if (held & (MOD_LALT | MOD_RALT)) {
        mods |= STATUS_MOD_OPT;
    }
    if (held & (MOD_LGUI | MOD_RGUI)) {
        mods |= STATUS_MOD_CMD;
    }
    if (held & (MOD_LSFT | MOD_RSFT)) {
        mods |= STATUS_MOD_SFT;
    }
    return mods;
}

void status_screen_draw(void) {
    struct zmk_endpoint_instance endpoint = zmk_endpoints_selected();
    zmk_keymap_layer_index_t layer = zmk_keymap_highest_layer_active();

    struct central_status status = {
        .battery = status_screen_battery_level(),
        .charging = status_screen_charging(),
        .peripheral_battery = peripheral_battery,
        .layer_name = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(layer)),
        .layer_index = layer,
        .mods = status_mods(),
    };

    if (endpoint.transport == ZMK_TRANSPORT_USB) {
        status.output = STATUS_OUTPUT_USB;
    } else {
        status.profile = endpoint.ble.profile_index + 1;
        if (zmk_ble_active_profile_is_connected()) {
            status.output = STATUS_OUTPUT_BT_LINKED;
        } else if (zmk_ble_active_profile_is_open()) {
            status.output = STATUS_OUTPUT_BT_PAIR;
        } else {
            status.output = STATUS_OUTPUT_BT_SEARCH;
        }
    }

    layout_central(&status);
}

static int keycode_listener_cb(const zmk_event_t *eh) {
    const struct zmk_keycode_state_changed *ev = as_zmk_keycode_state_changed(eh);

    if (ev->usage_page != HID_USAGE_KEY || ev->keycode < HID_USAGE_KEY_KEYBOARD_LEFTCONTROL ||
        ev->keycode > HID_USAGE_KEY_KEYBOARD_RIGHT_GUI) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    uint8_t bit = BIT(ev->keycode - HID_USAGE_KEY_KEYBOARD_LEFTCONTROL);
    atomic_val_t old = ev->state ? atomic_or(&held_mods, bit) : atomic_and(&held_mods, ~bit);
    if (((old & bit) != 0) != ev->state) {
        status_screen_redraw();
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(status_screen_mods, keycode_listener_cb);
ZMK_SUBSCRIPTION(status_screen_mods, zmk_keycode_state_changed);

static int status_listener_cb(const zmk_event_t *eh) {
#if IS_ENABLED(CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING)
    const struct zmk_peripheral_battery_state_changed *ev =
        as_zmk_peripheral_battery_state_changed(eh);
    if (ev != NULL) {
        peripheral_battery = ev->state_of_charge;
    }
#endif

    status_screen_redraw();
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(status_screen_central, status_listener_cb);
ZMK_SUBSCRIPTION(status_screen_central, zmk_layer_state_changed);
ZMK_SUBSCRIPTION(status_screen_central, zmk_endpoint_changed);
ZMK_SUBSCRIPTION(status_screen_central, zmk_ble_active_profile_changed);
#if IS_ENABLED(CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING)
ZMK_SUBSCRIPTION(status_screen_central, zmk_peripheral_battery_state_changed);
#endif
