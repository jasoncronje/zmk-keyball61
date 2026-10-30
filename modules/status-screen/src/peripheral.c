/*
 * Left half (peripheral): battery, link to the right half and Touch ID.
 *
 *   BAT  [bolt]   this half's battery, big
 *   LINK          OK or LOST
 *   TID  A/ON/OFF fingerprint, crossed out while Touch ID is unpowered; under
 *                 it a bar shrinking through the off countdown, or dashes in
 *                 always-on mode; then the minutes left, READY or ASLEEP
 */

#include <stdio.h>

#include <zephyr/kernel.h>

#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/split_peripheral_status_changed.h>
#include <zmk/split/bluetooth/peripheral.h>

#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_POWER)
#include <keyball61/touchid_power.h>
#endif

#include "draw.h"
#include "status_screen.h"

#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_POWER)
#define PRINT_X 1
#define PRINT_Y 68

#define BAR_WIDTH 30
#define BAR_Y (PRINT_Y + 30)
#define BAR_HEIGHT 2

#define OFF_DELAY_MS (CONFIG_KEYBALL61_TOUCHID_OFF_DELAY_SEC * 1000U)
// One redraw per pixel of bar width
#define BAR_STEP K_MSEC(OFF_DELAY_MS / BAR_WIDTH)

// Always-on dashes: 2 px on, 2 px off, across the bar's width
#define DASH_WIDTH 2
#define DASH_PITCH 4

static void draw_touchid(void) {
    enum keyball61_touchid_mode mode = keyball61_touchid_mode();
    bool on = keyball61_touchid_is_on();
    uint32_t remaining_ms = keyball61_touchid_off_remaining_ms();

    static const char *const mode_labels[] = {
        [KEYBALL61_TOUCHID_AUTO] = "A",
        [KEYBALL61_TOUCHID_ON] = "ON",
        [KEYBALL61_TOUCHID_OFF] = "OFF",
    };
    draw_header("TID", 52, mode_labels[mode], false);

    draw_glyph(on ? &icon_fingerprint_on : &icon_fingerprint_off, PRINT_X, PRINT_Y, true);

    if (mode == KEYBALL61_TOUCHID_ON) {
        for (int x = 0; x < BAR_WIDTH; x += DASH_PITCH) {
            draw_rect(PRINT_X + x, BAR_Y, DASH_WIDTH, BAR_HEIGHT, true);
        }
    } else if (on && remaining_ms > 0) {
        int width = DIV_ROUND_UP((uint64_t)BAR_WIDTH * remaining_ms, OFF_DELAY_MS);
        width = CLAMP(width, 1, BAR_WIDTH);
        draw_rect(PRINT_X + (BAR_WIDTH - width) / 2, BAR_Y, width, BAR_HEIGHT, true);

        char minutes[8];
        snprintf(minutes, sizeof(minutes), "%uM", DIV_ROUND_UP(remaining_ms, 60000U));
        draw_text_centered(minutes, 108, true);
        return;
    }

    draw_text_centered(on ? "READY" : "ASLEEP", 108, true);
}

static void touchid_redraw_work_cb(struct k_work *work);

static K_WORK_DELAYABLE_DEFINE(touchid_redraw_work, touchid_redraw_work_cb);

static void touchid_redraw_work_cb(struct k_work *work) {
    status_screen_redraw();

    // Keep shrinking the bar while the countdown runs
    if (keyball61_touchid_off_remaining_ms() > 0) {
        k_work_reschedule_for_queue(zmk_display_work_q(), &touchid_redraw_work, BAR_STEP);
    }
}

void keyball61_touchid_display_update(void) {
    k_work_reschedule_for_queue(zmk_display_work_q(), &touchid_redraw_work, K_NO_WAIT);
}
#endif

void status_screen_draw(void) {
    draw_header("BAT", 0, NULL, status_screen_charging());
    draw_big_percent(status_screen_battery_level(), 12);

    draw_header("LINK", 28, NULL, false);
    draw_text_centered(zmk_split_bt_peripheral_is_connected() ? "OK" : "LOST", 40, true);

#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_POWER)
    draw_touchid();
#endif
}

static int link_listener_cb(const zmk_event_t *eh) {
    status_screen_redraw();
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(status_screen_link, link_listener_cb);
ZMK_SUBSCRIPTION(status_screen_link, zmk_split_peripheral_status_changed);
