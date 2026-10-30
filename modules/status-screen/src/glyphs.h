#pragma once

#include <stdint.h>

// A 1-bit bitmap: one word per row, the leftmost pixel in bit w - 1
struct glyph {
    uint8_t w;
    uint8_t h;
    const uint32_t *rows;
};

// 5 px caps font, indexed by character - ' '; NULL where a character isn't drawn
extern const struct glyph *const small_font[96];

// 6x9 digits, drawn on an 8 px pitch
extern const struct glyph *const big_digits[10];

extern const struct glyph icon_bolt;
extern const struct glyph icon_ctl;
extern const struct glyph icon_opt;
extern const struct glyph icon_cmd;
extern const struct glyph icon_sft;
extern const struct glyph icon_fingerprint_on;
extern const struct glyph icon_fingerprint_off;
