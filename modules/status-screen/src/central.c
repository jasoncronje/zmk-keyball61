/*
 * Right half (central): battery for both halves, output, layer and held mods.
 *
 *   BAT  [bolt]   this half's battery, big, then the left half's
 *   BT n / USB    LINKED, SEARCH or PAIR / WIRED
 *   LAYER         highest active layer's name
 *   MODS          CTL OPT CMD SFT, lit while held
 */

#include <stdio.h>
#include <string.h>

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

#include "draw.h"
#include "status_screen.h"

// Modifier keys held down, as MOD_* bits; tracked from key events rather than
// the HID report, which other listeners may not have updated yet
static atomic_t held_mods;

// The left half's battery; 0 until it first reports
static uint8_t peripheral_battery;

static const struct {
    const char *label;
    const struct glyph *icon;
    uint8_t mods;
} mod_rows[] = {
    {"CTL", &icon_ctl, MOD_LCTL | MOD_RCTL},
    {"OPT", &icon_opt, MOD_LALT | MOD_RALT},
    {"CMD", &icon_cmd, MOD_LGUI | MOD_RGUI},
    {"SFT", &icon_sft, MOD_LSFT | MOD_RSFT},
};

// Names too wide for the screen, as they're shown
static const struct {
    const char *name;
    const char *shown;
} layer_short_names[] = {
    {"FUNCTION", "FN"},
    {"HSCROLL", "HSCRL"},
};

static void draw_battery(void) {
    draw_header("BAT", 0, NULL, status_screen_charging());
    draw_big_percent(status_screen_battery_level(), 11);

    char text[8];
    if (peripheral_battery > 0) {
        snprintf(text, sizeof(text), "L %u%%", peripheral_battery);
    } else {
        strcpy(text, "L --");
    }
    draw_text_centered(text, 22, true);
}

static void draw_output(void) {
    struct zmk_endpoint_instance endpoint = zmk_endpoints_selected();

    if (endpoint.transport == ZMK_TRANSPORT_USB) {
        draw_header("USB", 28, NULL, false);
        draw_text_centered("WIRED", 40, true);
        return;
    }

    char profile[4];
    snprintf(profile, sizeof(profile), "%d", endpoint.ble.profile_index + 1);
    draw_header("BT", 28, profile, false);

    if (zmk_ble_active_profile_is_connected()) {
        draw_text_centered("LINKED", 40, true);
    } else if (zmk_ble_active_profile_is_open()) {
        draw_text_centered("PAIR", 40, true);
    } else {
        draw_text_centered("SEARCH", 40, true);
    }
}

static void draw_layer(void) {
    draw_header("LAYER", 52, NULL, false);

    zmk_keymap_layer_index_t index = zmk_keymap_highest_layer_active();
    const char *name = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index));

    char text[12];
    if (name == NULL || name[0] == '\0') {
        snprintf(text, sizeof(text), "%u", index);
    } else {
        for (size_t i = 0; i < ARRAY_SIZE(layer_short_names); i++) {
            if (strcmp(name, layer_short_names[i].name) == 0) {
                name = layer_short_names[i].shown;
                break;
            }
        }

        size_t len = 0;
        for (; name[len] != '\0' && len < sizeof(text) - 1; len++) {
            char c = name[len];
            text[len] = (c >= 'a' && c <= 'z') ? c - 'a' + 'A' : c;
        }
        text[len] = '\0';

        // Cut anything else that doesn't fit
        while (len > 1 && draw_text_width(text) > SCREEN_W) {
            text[--len] = '\0';
        }
    }
    draw_text_centered(text, 64, true);
}

static void draw_mods(void) {
    draw_header("MODS", 76, NULL, false);

    uint8_t mods = atomic_get(&held_mods);
    for (size_t i = 0; i < ARRAY_SIZE(mod_rows); i++) {
        int y = 88 + i * 10;
        bool held = mods & mod_rows[i].mods;

        if (held) {
            draw_rect(0, y - 1, SCREEN_W, 9, true);
        }
        draw_glyph(mod_rows[i].icon, 2, y - 1, !held);
        draw_text(mod_rows[i].label, 15, y + 1, !held);
    }
}

void status_screen_draw(void) {
    draw_battery();
    draw_output();
    draw_layer();
    draw_mods();
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
