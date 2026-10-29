/*
 * Touch ID power: the Touch ID board runs from a TPS61023 5 V boost fed by the
 * battery. Its En pin is driven here so the boost (and the Touch ID board) is on
 * while the keyboard is active and off a while after it goes idle (auto mode).
 * Plugging in USB switches to always-on mode and unplugging switches back to
 * auto; the &touchid behavior can pick another mode in between. In shutdown
 * the TPS61023 disconnects its output, so the Touch ID board draws nothing.
 */

#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <zmk/activity.h>
#include <zmk/event_manager.h>
#include <zmk/events/activity_state_changed.h>

#include <dt-bindings/keyball61/touchid.h>

#include "touchid_power.h"

#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/usb.h>
#endif

LOG_MODULE_REGISTER(touchid_power, CONFIG_ZMK_LOG_LEVEL);

static const struct gpio_dt_spec en = GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), touchid_en_gpios);

// The keyboard starts active, so Touch ID starts on
static bool touchid_on = true;

// Every reset starts back in auto (or always-on once USB power is seen), so a
// forgotten off can't stick
static enum keyball61_touchid_mode mode = KEYBALL61_TOUCHID_AUTO;

bool keyball61_touchid_is_on(void) { return touchid_on; }

enum keyball61_touchid_mode keyball61_touchid_mode(void) { return mode; }

static void notify_display(void) {
#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_DISPLAY_ICON)
    keyball61_touchid_display_update();
#endif
}

static void touchid_power_set(bool on) {
    LOG_DBG("Touch ID power %s", on ? "on" : "off");
    gpio_pin_set_dt(&en, on);

    if (on == touchid_on) {
        return;
    }
    touchid_on = on;
    notify_display();
}

static void touchid_off_work_cb(struct k_work *work) { touchid_power_set(false); }

static K_WORK_DELAYABLE_DEFINE(touchid_off_work, touchid_off_work_cb);

uint32_t keyball61_touchid_off_remaining_ms(void) {
    if (!k_work_delayable_is_pending(&touchid_off_work)) {
        return 0;
    }
    return (uint32_t)k_ticks_to_ms_ceil64(k_work_delayable_remaining_get(&touchid_off_work));
}

static void start_off_countdown(void) {
    k_work_reschedule(&touchid_off_work, K_SECONDS(CONFIG_KEYBALL61_TOUCHID_OFF_DELAY_SEC));
    notify_display();
}

static void cancel_off_countdown(void) {
    bool was_counting = k_work_delayable_is_pending(&touchid_off_work);
    k_work_cancel_delayable(&touchid_off_work);
    if (was_counting && touchid_on) {
        // Power isn't changing, but the countdown bar has to go
        notify_display();
    }
}

static void touchid_keep_on(void) {
    cancel_off_countdown();
    touchid_power_set(true);
}

// Brings the power in line with the mode and activity
static void touchid_update(void) {
    switch (mode) {
    case KEYBALL61_TOUCHID_ON:
        touchid_keep_on();
        break;
    case KEYBALL61_TOUCHID_OFF:
        cancel_off_countdown();
        touchid_power_set(false);
        break;
    case KEYBALL61_TOUCHID_AUTO:
        if (zmk_activity_get_state() == ZMK_ACTIVITY_ACTIVE) {
            touchid_keep_on();
        } else if (touchid_on && !k_work_delayable_is_pending(&touchid_off_work)) {
            // Idle, e.g. just unplugged: count down from now
            start_off_countdown();
        }
        break;
    }
}

static void set_mode(enum keyball61_touchid_mode new_mode) {
    bool changed = new_mode != mode;
    mode = new_mode;

    LOG_INF("Touch ID mode %d", mode);
    touchid_update();
    if (changed) {
        // The icon shows the mode even when the power doesn't change
        notify_display();
    }
}

#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
static bool was_usb_powered;
#endif

static uint32_t pending_command;

static void touchid_command_work_cb(struct k_work *work) {
    switch (pending_command) {
    case TID_AUTO:
        set_mode(KEYBALL61_TOUCHID_AUTO);
        break;
    case TID_ON:
        set_mode(KEYBALL61_TOUCHID_ON);
        break;
    case TID_OFF:
        set_mode(KEYBALL61_TOUCHID_OFF);
        break;
    case TID_CYCLE:
        set_mode((mode + 1) % (KEYBALL61_TOUCHID_OFF + 1));
        break;
    }
}

static K_WORK_DEFINE(touchid_command_work, touchid_command_work_cb);

void keyball61_touchid_command(uint32_t command) {
    // Runs on the split transport's thread; the listener runs on the system work
    // queue, so apply the command there too
    pending_command = command;
    k_work_submit(&touchid_command_work);
}

static int touchid_power_listener(const zmk_event_t *eh) {
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    if (as_zmk_usb_conn_state_changed(eh) != NULL) {
        // The event also fires for host suspend and resume, so act only when power
        // comes or goes, and keep a mode picked with the key until then
        bool powered = zmk_usb_is_powered();
        if (powered != was_usb_powered) {
            was_usb_powered = powered;
            set_mode(powered ? KEYBALL61_TOUCHID_ON : KEYBALL61_TOUCHID_AUTO);
        }
        return ZMK_EV_EVENT_BUBBLE;
    }
#endif

    const struct zmk_activity_state_changed *ev = as_zmk_activity_state_changed(eh);
    if (ev == NULL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (ev->state == ZMK_ACTIVITY_SLEEP) {
        // Deep sleep keeps GPIO outputs, so the boost stays off until the next wake resets us
        cancel_off_countdown();
        touchid_power_set(false);
    } else {
        touchid_update();
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(touchid_power, touchid_power_listener);
ZMK_SUBSCRIPTION(touchid_power, zmk_activity_state_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(touchid_power, zmk_usb_conn_state_changed);
#endif

static int touchid_power_init(void) {
    if (!gpio_is_ready_dt(&en)) {
        LOG_ERR("Touch ID enable GPIO not ready");
        return -ENODEV;
    }

    // The keyboard starts active, so start with Touch ID on
    return gpio_pin_configure_dt(&en, GPIO_OUTPUT_ACTIVE);
}

SYS_INIT(touchid_power_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
