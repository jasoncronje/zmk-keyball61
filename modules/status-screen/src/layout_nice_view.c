/*
 * The 160x68 nice!view, read in portrait (68x160) in labelled blocks: the
 * OLED's 5 px headers, with values drawn twice the size.
 *
 * Right half:
 *   BT n / USB    LINKED, SEARCH or PAIR / WIRED
 *   BAT  [bolt]   this half's battery, big, then the left half's
 *   LAYER         highest active layer's name
 *   MODS          2x2 grid of the Mac modifier symbols, a cell lit while held
 *
 * Left half:
 *   BAT  [bolt]   this half's battery, big
 *   LINK          OK or LOST
 *   TID  A/ON/OFF fingerprint, crossed out while Touch ID is unpowered; under
 *                 it a bar shrinking through the off countdown, or dashes in
 *                 always-on mode; then the minutes left, READY or ASLEEP
 */

#include <stdio.h>
#include <string.h>

#include <zephyr/sys/util.h>

#include "draw.h"
#include "layout.h"

// Values are the 5 px font at this scale
#define VALUE_SCALE 2

static void draw_output(const struct central_status *s, int y) {
    if (s->output == STATUS_OUTPUT_USB) {
        draw_header("USB", y, NULL, false);
        draw_text_centered_scaled("WIRED", y + 11, VALUE_SCALE, true);
        return;
    }

    char profile[12];
    snprintf(profile, sizeof(profile), "%d", s->profile);
    draw_header("BT", y, profile, false);

    const char *state = s->output == STATUS_OUTPUT_BT_LINKED ? "LINKED"
                        : s->output == STATUS_OUTPUT_BT_PAIR ? "PAIR"
                                                             : "SEARCH";
    draw_text_centered_scaled(state, y + 11, VALUE_SCALE, true);
}

static void draw_battery(const struct central_status *s, int y) {
    draw_header("BAT", y, NULL, s->charging);
    draw_big_percent_scaled(s->battery, y + 11, 2);

    char text[8];
    if (s->peripheral_battery > 0) {
        snprintf(text, sizeof(text), "L %u%%", s->peripheral_battery);
    } else {
        strcpy(text, "L --");
    }
    draw_text_centered_scaled(text, y + 33, VALUE_SCALE, true);
}

static void draw_layer(const struct central_status *s, int y) {
    draw_header("LAYER", y, NULL, false);

    char text[12];
    // Kept off the edges: HSCROLL would fill the width exactly
    layout_layer_text(s, VALUE_SCALE, SCREEN_W - 6, text, sizeof(text));
    draw_text_centered_scaled(text, y + 11, VALUE_SCALE, true);
}

#define MOD_CELL_W 33
#define MOD_CELL_H 24
#define MOD_CELL_GAP 2

static const struct {
    const struct glyph *icon;
    uint8_t mods;
} mod_cells[] = {
    {&icon_ctl, STATUS_MOD_CTL},
    {&icon_opt, STATUS_MOD_OPT},
    {&icon_cmd, STATUS_MOD_CMD},
    {&icon_sft, STATUS_MOD_SFT},
};

static void draw_mods(const struct central_status *s, int y) {
    draw_header("MODS", y, NULL, false);

    for (size_t i = 0; i < ARRAY_SIZE(mod_cells); i++) {
        int x = (i % 2) * (MOD_CELL_W + MOD_CELL_GAP);
        int cy = y + 11 + (i / 2) * (MOD_CELL_H + MOD_CELL_GAP);
        bool held = s->mods & mod_cells[i].mods;
        const struct glyph *icon = mod_cells[i].icon;

        if (held) {
            draw_rect(x, cy, MOD_CELL_W, MOD_CELL_H, true);
        } else {
            draw_frame(x, cy, MOD_CELL_W, MOD_CELL_H, true);
        }
        draw_glyph_scaled(icon, x + (MOD_CELL_W - icon->w * 2) / 2,
                          cy + (MOD_CELL_H - icon->h * 2) / 2, 2, !held);
    }
}

void layout_central(const struct central_status *status) {
    draw_output(status, 0);
    draw_battery(status, 25);
    draw_layer(status, 72);
    draw_mods(status, 97);
}

#define PRINT_SCALE 2
#define PRINT_X ((SCREEN_W - LAYOUT_TOUCHID_BAR_WIDTH) / 2)

#define BAR_HEIGHT 3

// Always-on dashes: 4 px on, 4 px off, across the bar's width
#define DASH_WIDTH 4
#define DASH_PITCH 8

static void draw_touchid(const struct peripheral_status *s, int y) {
    static const char *const mode_labels[] = {
        [KEYBALL61_TOUCHID_AUTO] = "A",
        [KEYBALL61_TOUCHID_ON] = "ON",
        [KEYBALL61_TOUCHID_OFF] = "OFF",
    };
    draw_header("TID", y, mode_labels[s->touchid_mode], false);

    const struct glyph *print = s->touchid_on ? &icon_fingerprint_on : &icon_fingerprint_off;
    int print_y = y + 11;
    draw_glyph_scaled(print, PRINT_X, print_y, PRINT_SCALE, true);

    int bar_y = print_y + print->h * PRINT_SCALE + 3;
    int text_y = bar_y + BAR_HEIGHT + 5;

    if (s->touchid_mode == KEYBALL61_TOUCHID_ON) {
        for (int x = 0; x < LAYOUT_TOUCHID_BAR_WIDTH; x += DASH_PITCH) {
            draw_rect(PRINT_X + x, bar_y, DASH_WIDTH, BAR_HEIGHT, true);
        }
    } else if (s->touchid_on && s->touchid_remaining_ms > 0) {
        int width = DIV_ROUND_UP((uint64_t)LAYOUT_TOUCHID_BAR_WIDTH * s->touchid_remaining_ms,
                                 s->touchid_off_delay_ms);
        width = CLAMP(width, 1, LAYOUT_TOUCHID_BAR_WIDTH);
        draw_rect(PRINT_X + (LAYOUT_TOUCHID_BAR_WIDTH - width) / 2, bar_y, width, BAR_HEIGHT,
                  true);

        char minutes[8];
        snprintf(minutes, sizeof(minutes), "%uM", DIV_ROUND_UP(s->touchid_remaining_ms, 60000U));
        draw_text_centered_scaled(minutes, text_y, VALUE_SCALE, true);
        return;
    }

    draw_text_centered_scaled(s->touchid_on ? "READY" : "ASLEEP", text_y, VALUE_SCALE, true);
}

void layout_peripheral(const struct peripheral_status *status) {
    draw_header("BAT", 0, NULL, status->charging);
    draw_big_percent_scaled(status->battery, 11, 2);

    draw_header("LINK", 33, NULL, false);
    draw_text_centered_scaled(status->linked ? "OK" : "LOST", 44, VALUE_SCALE, true);

    if (status->touchid) {
        draw_touchid(status, 58);
    }
}
