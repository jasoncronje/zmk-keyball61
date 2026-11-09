/*
 * Drawing onto the status screen as it's read: a portrait 1-bit frame, x across
 * its width, y down its length. 32x128 on the OLED, 68x160 on the nice!view.
 * status_screen.c turns it into the panel's landscape canvas.
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "glyphs.h"

#ifdef CONFIG_KEYBALL61_STATUS_SCREEN_NICE_VIEW
#define SCREEN_W 68
#define SCREEN_H 160
#else
#define SCREEN_W 32
#define SCREEN_H 128
#endif

void draw_clear(void);
bool draw_get(int x, int y);
void draw_rect(int x, int y, int w, int h, bool on);
// A 1 px outline
void draw_frame(int x, int y, int w, int h, bool on);
void draw_glyph(const struct glyph *g, int x, int y, bool on);
// Each glyph pixel drawn as a scale x scale block
void draw_glyph_scaled(const struct glyph *g, int x, int y, int scale, bool on);

// Small 5 px caps text, or 5 * scale px; returns the width it takes
int draw_text_width(const char *text);
int draw_text_width_scaled(const char *text, int scale);
void draw_text(const char *text, int x, int y, bool on);
void draw_text_scaled(const char *text, int x, int y, int scale, bool on);
void draw_text_centered(const char *text, int y, bool on);
void draw_text_centered_scaled(const char *text, int y, int scale, bool on);
void draw_text_right(const char *text, int right, int y, bool on);

// A lit 9 px bar with a dark label on the left and optional text or bolt on the right
void draw_header(const char *label, int y, const char *right, bool bolt);

// A battery level in big digits with a small %, centred
void draw_big_percent(uint8_t level, int y);
void draw_big_percent_scaled(uint8_t level, int y, int scale);
