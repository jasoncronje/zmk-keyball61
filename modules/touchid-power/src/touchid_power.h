#pragma once

#include <stdbool.h>

bool keyball61_touchid_is_on(void);

// Schedules a redraw on the display work queue after the power state changes
void keyball61_touchid_display_update(void);
