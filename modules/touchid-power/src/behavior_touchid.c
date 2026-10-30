/*
 * &touchid behavior: sets the Touch ID power mode from the keymap. Global
 * locality, so the central forwards each press to the left half, which owns the
 * boost converter. On halves without Touch ID power it does nothing.
 */

#define DT_DRV_COMPAT zmk_behavior_touchid

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/logging/log.h>

#include <drivers/behavior.h>

#include <dt-bindings/keyball61/touchid.h>

#include <keyball61/touchid_power.h>

LOG_MODULE_REGISTER(behavior_touchid, CONFIG_ZMK_LOG_LEVEL);

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

static const struct behavior_parameter_value_metadata std_values[] = {
    {
        .value = TID_CYCLE,
        .display_name = "Cycle Auto/On/Off",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = TID_AUTO,
        .display_name = "Auto",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = TID_ON,
        .display_name = "Always On",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
    {
        .value = TID_OFF,
        .display_name = "Off",
        .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE,
    },
};

static const struct behavior_parameter_metadata_set std_set = {
    .param1_values = std_values,
    .param1_values_len = ARRAY_SIZE(std_values),
};

static const struct behavior_parameter_metadata metadata = {
    .sets_len = 1,
    .sets = &std_set,
};

#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    if (binding->param1 > TID_CYCLE) {
        LOG_ERR("Unknown Touch ID command: %d", binding->param1);
        return -ENOTSUP;
    }

#if IS_ENABLED(CONFIG_KEYBALL61_TOUCHID_POWER)
    keyball61_touchid_command(binding->param1);
#endif
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_keymap_binding_released(struct zmk_behavior_binding *binding,
                                      struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api behavior_touchid_driver_api = {
    .binding_pressed = on_keymap_binding_pressed,
    .binding_released = on_keymap_binding_released,
    .locality = BEHAVIOR_LOCALITY_GLOBAL,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .parameter_metadata = &metadata,
#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,
                        &behavior_touchid_driver_api);

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
