zephyr_include_directories(include)

target_sources_ifdef(CONFIG_KEYBALL61_TOUCHID_POWER app PRIVATE src/touchid_power.c)
# Built on both halves: the central resolves the binding and forwards it to the left half
target_sources_ifdef(CONFIG_DT_HAS_ZMK_BEHAVIOR_TOUCHID_ENABLED app PRIVATE src/behavior_touchid.c)
