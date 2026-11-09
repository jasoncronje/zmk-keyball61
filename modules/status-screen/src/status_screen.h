#pragma once

#include <stdbool.h>
#include <stdint.h>

// Queues a full redraw on the display work queue; safe from any thread
void status_screen_redraw(void);

// This half's own battery
uint8_t status_screen_battery_level(void);
bool status_screen_charging(void);

// Draws this half's screen with draw.h; central.c or peripheral.c, on the display work queue
void status_screen_draw(void);

// Left half: the active layer's name, handed over by the right half (layer_sync.c)
void status_screen_set_layer_name(const char *name);
