/*
 * Shows the active layer on the left half, whose firmware has no keymap. On
 * each layer change the right half invokes the &lyrsync behavior with the
 * layer's name packed into its two params, four characters each. Its global
 * locality makes ZMK's split forward it to the left half, whose status screen
 * shows the name. The right half sends it again after each connection, since
 * a left half that reconnects has missed the changes.
 */

#define DT_DRV_COMPAT zmk_behavior_layer_sync

#include <stdio.h>
#include <string.h>

#include <zephyr/bluetooth/conn.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>

#include <drivers/behavior.h>

#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/keymap.h>

#include "status_screen.h"

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#define IS_CENTRAL (!IS_ENABLED(CONFIG_ZMK_SPLIT) || IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL))

// Fits both params; longer names are cut
#define NAME_LEN 8

static void unpack_name(const struct zmk_behavior_binding *binding, char name[NAME_LEN + 1]) {
    for (int i = 0; i < NAME_LEN; i++) {
        uint32_t param = i < 4 ? binding->param1 : binding->param2;
        name[i] = (param >> (8 * (i % 4))) & 0xff;
    }
    name[NAME_LEN] = '\0';
}

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
#if !IS_CENTRAL
    char name[NAME_LEN + 1];
    unpack_name(binding, name);
    status_screen_set_layer_name(name);
#endif
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_keymap_binding_released(struct zmk_behavior_binding *binding,
                                      struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api behavior_layer_sync_driver_api = {
    .binding_pressed = on_keymap_binding_pressed,
    .binding_released = on_keymap_binding_released,
    .locality = BEHAVIOR_LOCALITY_GLOBAL,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = zmk_behavior_get_empty_param_metadata,
#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,
                        &behavior_layer_sync_driver_api);

#if IS_CENTRAL

// Long enough after connecting for the split link's GATT discovery; sent
// twice in case the first lands before it finishes
#define RESEND_FIRST K_SECONDS(3)
#define RESEND_SECOND K_SECONDS(10)

// The name last sent, so a layer change that keeps the top layer sends nothing
static char sent_name[NAME_LEN + 1];

static void send_layer(bool force) {
    zmk_keymap_layer_index_t index = zmk_keymap_highest_layer_active();
    const char *layer_name = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index));

    char name[NAME_LEN + 1] = {0};
    if (layer_name == NULL || layer_name[0] == '\0') {
        snprintf(name, sizeof(name), "%u", index);
    } else {
        strncpy(name, layer_name, NAME_LEN);
    }

    if (!force && strcmp(name, sent_name) == 0) {
        return;
    }
    strcpy(sent_name, name);

    struct zmk_behavior_binding binding = {
        .behavior_dev = DEVICE_DT_NAME(DT_DRV_INST(0)),
    };
    for (int i = 0; i < NAME_LEN; i++) {
        uint32_t *param = i < 4 ? &binding.param1 : &binding.param2;
        *param |= (uint32_t)(uint8_t)name[i] << (8 * (i % 4));
    }

    struct zmk_behavior_binding_event event = {
        .layer = index,
        .timestamp = k_uptime_get(),
#if IS_ENABLED(CONFIG_ZMK_SPLIT)
        .source = ZMK_POSITION_STATE_CHANGE_SOURCE_LOCAL,
#endif
    };
    zmk_behavior_invoke_binding(&binding, event, true);
}

static void layer_work_cb(struct k_work *work) { send_layer(false); }

static K_WORK_DEFINE(layer_work, layer_work_cb);

static void resend_work_cb(struct k_work *work) { send_layer(true); }

static K_WORK_DELAYABLE_DEFINE(resend_first_work, resend_work_cb);
static K_WORK_DELAYABLE_DEFINE(resend_second_work, resend_work_cb);

static int layer_listener_cb(const zmk_event_t *eh) {
    k_work_submit(&layer_work);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(layer_sync, layer_listener_cb);
ZMK_SUBSCRIPTION(layer_sync, zmk_layer_state_changed);

// Any connection, to the host or to the left half; resending is harmless
static void connected(struct bt_conn *conn, uint8_t err) {
    if (err) {
        return;
    }
    k_work_reschedule(&resend_first_work, RESEND_FIRST);
    k_work_reschedule(&resend_second_work, RESEND_SECOND);
}

BT_CONN_CB_DEFINE(layer_sync_conn_callbacks) = {
    .connected = connected,
};

#endif // IS_CENTRAL

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
