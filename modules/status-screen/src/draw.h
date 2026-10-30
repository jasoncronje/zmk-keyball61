/*
 * Drawing onto the status screen as it's read: a portrait 32x128 1-bit frame,
 * x across the 32 px width, y down the 128 px length. status_screen.c turns it
 * into the panel's landscape canvas.
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "glyphs.h"

#define SCREEN_W 32
#define SCREEN_H 128

void draw_clear(void);
bool draw_get(int x, int y);
void draw_rect(int x, int y, int w, int h, bool on);
void draw_glyph(const struct glyph *g, int x, int y, bool on);

// Small 5 px caps text; returns the width it takes
int draw_text_width(const char *text);
void draw_text(const char *text, int x, int y, bool on);
void draw_text_centered(const char *text, int y, bool on);
void draw_text_right(const char *text, int right, int y, bool on);

// A lit 9 px bar with a dark label on the left and optional text or bolt on the right
void draw_header(const char *label, int y, const char *right, bool bolt);

// A battery level in big digits with a small %, centred
void draw_big_percent(uint8_t level, int y);
