#pragma once

#include <stdbool.h>
#include <stdint.h>

enum keyball61_touchid_mode {
    // On while active or on USB power, off a while after the keyboard goes idle
    KEYBALL61_TOUCHID_AUTO,
    // On until deep sleep, whatever the activity
    KEYBALL61_TOUCHID_ON,
    // Off, even on USB power or while typing
    KEYBALL61_TOUCHID_OFF,
};

bool keyball61_touchid_is_on(void);

enum keyball61_touchid_mode keyball61_touchid_mode(void);

// Applies a TID_* command from dt-bindings/keyball61/touchid.h
void keyball61_touchid_command(uint32_t command);

// Time left before Touch ID switches off, or 0 when no countdown is running
uint32_t keyball61_touchid_off_remaining_ms(void);

// Schedules a redraw on the display work queue after the power state changes
void keyball61_touchid_display_update(void);
