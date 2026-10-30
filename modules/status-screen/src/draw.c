#include <stdio.h>
#include <string.h>

#include <zephyr/sys/util.h>

#include "draw.h"

// One bit per pixel, a word per row, x = 0 in bit 31
static uint32_t frame[SCREEN_H];

#define BIG_PITCH 8

void draw_clear(void) { memset(frame, 0, sizeof(frame)); }

bool draw_get(int x, int y) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) {
        return false;
    }
    return frame[y] & (1U << (31 - x));
}

static void draw_px(int x, int y, bool on) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) {
        return;
    }
    if (on) {
        frame[y] |= 1U << (31 - x);
    } else {
        frame[y] &= ~(1U << (31 - x));
    }
}

void draw_rect(int x, int y, int w, int h, bool on) {
    for (int j = y; j < y + h; j++) {
        for (int i = x; i < x + w; i++) {
            draw_px(i, j, on);
        }
    }
}

// Only the glyph's set pixels are drawn, so it can go over a lit background
void draw_glyph(const struct glyph *g, int x, int y, bool on) {
    for (int j = 0; j < g->h; j++) {
        for (int i = 0; i < g->w; i++) {
            if (g->rows[j] & (1U << (g->w - 1 - i))) {
                draw_px(x + i, y + j, on);
            }
        }
    }
}

static const struct glyph *small_glyph(char c) {
    // Wraps around for anything below ' '
    unsigned int index = (unsigned char)c - ' ';
    return index < ARRAY_SIZE(small_font) ? small_font[index] : NULL;
}

int draw_text_width(const char *text) {
    int width = 0;
    for (const char *c = text; *c; c++) {
        const struct glyph *g = small_glyph(*c);
        if (g) {
            width += g->w + 1;
        }
    }
    return width > 0 ? width - 1 : 0;
}

void draw_text(const char *text, int x, int y, bool on) {
    for (const char *c = text; *c; c++) {
        const struct glyph *g = small_glyph(*c);
        if (g) {
            draw_glyph(g, x, y, on);
            x += g->w + 1;
        }
    }
}

void draw_text_centered(const char *text, int y, bool on) {
    int x = (SCREEN_W - draw_text_width(text)) / 2;
    draw_text(text, x > 0 ? x : 0, y, on);
}

void draw_text_right(const char *text, int right, int y, bool on) {
    draw_text(text, right - draw_text_width(text), y, on);
}

void draw_header(const char *label, int y, const char *right, bool bolt) {
    draw_rect(0, y, SCREEN_W, 9, true);
    draw_text(label, 2, y + 2, false);
    if (bolt) {
        draw_glyph(&icon_bolt, 25, y + 1, false);
    } else if (right) {
        draw_text_right(right, 30, y + 2, false);
    }
}

void draw_big_percent(uint8_t level, int y) {
    char digits[4];
    int n = snprintf(digits, sizeof(digits), "%u", level > 100 ? 100 : level);

    int digits_w = n * BIG_PITCH;
    int x = (SCREEN_W - (digits_w + 7)) / 2;
    for (int i = 0; i < n; i++) {
        draw_glyph(big_digits[digits[i] - '0'], x + i * BIG_PITCH, y, true);
    }
    draw_text("%", x + digits_w + 2, y + 4, true);
}
