#pragma once

#include <stdbool.h>
#include <stdint.h>

bool keyball61_touchid_is_on(void);

// Time left before Touch ID switches off, or 0 when no countdown is running
uint32_t keyball61_touchid_off_remaining_ms(void);

// Schedules a redraw on the display work queue after the power state changes
void keyball61_touchid_display_update(void);
