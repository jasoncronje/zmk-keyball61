#include <stdio.h>
#include <string.h>

#include <zephyr/sys/util.h>

#include "draw.h"

#define ROW_BYTES ((SCREEN_W + 7) / 8)

// One bit per pixel, x = 0 in the first byte's top bit
static uint8_t frame[SCREEN_H][ROW_BYTES];

#define BIG_PITCH 8

void draw_clear(void) { memset(frame, 0, sizeof(frame)); }

bool draw_get(int x, int y) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) {
        return false;
    }
    return frame[y][x / 8] & (0x80 >> (x % 8));
}

static void draw_px(int x, int y, bool on) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) {
        return;
    }
    if (on) {
        frame[y][x / 8] |= 0x80 >> (x % 8);
    } else {
        frame[y][x / 8] &= ~(0x80 >> (x % 8));
    }
}

void draw_rect(int x, int y, int w, int h, bool on) {
    for (int j = y; j < y + h; j++) {
        for (int i = x; i < x + w; i++) {
            draw_px(i, j, on);
        }
    }
}

void draw_frame(int x, int y, int w, int h, bool on) {
    draw_rect(x, y, w, 1, on);
    draw_rect(x, y + h - 1, w, 1, on);
    draw_rect(x, y, 1, h, on);
    draw_rect(x + w - 1, y, 1, h, on);
}

// Only the glyph's set pixels are drawn, so it can go over a lit background
void draw_glyph_scaled(const struct glyph *g, int x, int y, int scale, bool on) {
    for (int j = 0; j < g->h; j++) {
        for (int i = 0; i < g->w; i++) {
            if (g->rows[j] & (1U << (g->w - 1 - i))) {
                draw_rect(x + i * scale, y + j * scale, scale, scale, on);
            }
        }
    }
}

void draw_glyph(const struct glyph *g, int x, int y, bool on) {
    draw_glyph_scaled(g, x, y, 1, on);
}

static const struct glyph *small_glyph(char c) {
    // Wraps around for anything below ' '
    unsigned int index = (unsigned char)c - ' ';
    return index < ARRAY_SIZE(small_font) ? small_font[index] : NULL;
}

int draw_text_width_scaled(const char *text, int scale) {
    int width = 0;
    for (const char *c = text; *c; c++) {
        const struct glyph *g = small_glyph(*c);
        if (g) {
            width += (g->w + 1) * scale;
        }
    }
    return width > 0 ? width - scale : 0;
}

int draw_text_width(const char *text) { return draw_text_width_scaled(text, 1); }

void draw_text_scaled(const char *text, int x, int y, int scale, bool on) {
    for (const char *c = text; *c; c++) {
        const struct glyph *g = small_glyph(*c);
        if (g) {
            draw_glyph_scaled(g, x, y, scale, on);
            x += (g->w + 1) * scale;
        }
    }
}

void draw_text(const char *text, int x, int y, bool on) { draw_text_scaled(text, x, y, 1, on); }

void draw_text_centered_scaled(const char *text, int y, int scale, bool on) {
    int x = (SCREEN_W - draw_text_width_scaled(text, scale)) / 2;
    draw_text_scaled(text, x > 0 ? x : 0, y, scale, on);
}

void draw_text_centered(const char *text, int y, bool on) {
    draw_text_centered_scaled(text, y, 1, on);
}

void draw_text_right(const char *text, int right, int y, bool on) {
    draw_text(text, right - draw_text_width(text), y, on);
}

void draw_header(const char *label, int y, const char *right, bool bolt) {
    draw_rect(0, y, SCREEN_W, 9, true);
    draw_text(label, 2, y + 2, false);
    if (bolt) {
        draw_glyph(&icon_bolt, SCREEN_W - 7, y + 1, false);
    } else if (right) {
        draw_text_right(right, SCREEN_W - 2, y + 2, false);
    }
}

void draw_big_percent_scaled(uint8_t level, int y, int scale) {
    char digits[4];
    int n = snprintf(digits, sizeof(digits), "%u", level > 100 ? 100 : level);

    // The % sits 2 px after the digits and is 5 px wide
    int digits_w = n * BIG_PITCH * scale;
    int x = (SCREEN_W - (digits_w + 7 * scale)) / 2;
    for (int i = 0; i < n; i++) {
        draw_glyph_scaled(big_digits[digits[i] - '0'], x + i * BIG_PITCH * scale, y, scale, true);
    }
    draw_text_scaled("%", x + digits_w + 2 * scale, y + 4 * scale, scale, true);
}

void draw_big_percent(uint8_t level, int y) { draw_big_percent_scaled(level, y, 1); }
