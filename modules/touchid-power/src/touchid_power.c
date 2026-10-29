/*
 * Touch ID power: the Touch ID board runs from a TPS61023 5 V boost fed by the
 * battery. Its En pin is driven here so the boost (and the Touch ID board) is on
 * while the keyboard is active and off a while after it goes idle. While this
 * half has USB power it stays on regardless of idle. In shutdown the TPS61023
 * disconnects its output, so the Touch ID board draws nothing.
 */

#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <zmk/activity.h>
#include <zmk/event_manager.h>
#include <zmk/events/activity_state_changed.h>

#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/usb.h>
#endif

LOG_MODULE_REGISTER(touchid_power, CONFIG_ZMK_LOG_LEVEL);

static const struct gpio_dt_spec en = GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), touchid_en_gpios);

static void touchid_power_set(bool on) {
    LOG_DBG("Touch ID power %s", on ? "on" : "off");
    gpio_pin_set_dt(&en, on);
}

static void touchid_off_work_cb(struct k_work *work) { touchid_power_set(false); }

static K_WORK_DELAYABLE_DEFINE(touchid_off_work, touchid_off_work_cb);

static bool usb_powered(void) {
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    return zmk_usb_is_powered();
#else
    return false;
#endif
}

static void touchid_keep_on(void) {
    k_work_cancel_delayable(&touchid_off_work);
    touchid_power_set(true);
}

static int touchid_power_listener(const zmk_event_t *eh) {
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    if (as_zmk_usb_conn_state_changed(eh) != NULL) {
        if (usb_powered()) {
            touchid_keep_on();
        } else if (zmk_activity_get_state() != ZMK_ACTIVITY_ACTIVE) {
            // Unplugged while idle: start the off countdown from now
            k_work_reschedule(&touchid_off_work, K_SECONDS(CONFIG_KEYBALL61_TOUCHID_OFF_DELAY_SEC));
        }
        return ZMK_EV_EVENT_BUBBLE;
    }
#endif

    const struct zmk_activity_state_changed *ev = as_zmk_activity_state_changed(eh);
    if (ev == NULL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    switch (ev->state) {
    case ZMK_ACTIVITY_ACTIVE:
        touchid_keep_on();
        break;
    case ZMK_ACTIVITY_IDLE:
        // On USB power there's no battery to save, so Touch ID never switches off
        if (!usb_powered()) {
            k_work_reschedule(&touchid_off_work, K_SECONDS(CONFIG_KEYBALL61_TOUCHID_OFF_DELAY_SEC));
        }
        break;
    case ZMK_ACTIVITY_SLEEP:
        // Deep sleep keeps GPIO outputs, so the boost stays off until the next wake resets us
        k_work_cancel_delayable(&touchid_off_work);
        touchid_power_set(false);
        break;
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
