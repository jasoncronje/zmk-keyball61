/*
 * The 160x68 nice!view, read in portrait (68x160) in labelled blocks: the
 * OLED's 5 px headers, with values drawn twice the size. Both halves start
 * with the same battery block, and the right half's BT block lines up with the
 * left half's LINK.
 *
 * Right half:
 *   BAT  [bolt]   this half's battery, big, then the left half's
 *   BT n / USB    LINKED, SEARCH or PAIR / WIRED
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

// Each block: a 9 px header, then its value 2 px below
#define VALUE_Y(y) ((y) + 11)

// Block tops, matching across the halves
#define BATTERY_Y 0
#define LINK_Y 44
#define THIRD_Y 68
#define FOURTH_Y 92

// The battery block on both halves: header and the big percentage, with room
// below for the right half's line for the left half
static void draw_battery_block(uint8_t level, bool charging) {
    draw_header("BAT", BATTERY_Y, NULL, charging);
    draw_big_percent_scaled(level, VALUE_Y(BATTERY_Y), 2);
}

static void draw_output(const struct central_status *s, int y) {
    if (s->output == STATUS_OUTPUT_USB) {
        draw_header("USB", y, NULL, false);
        draw_text_centered_scaled("WIRED", VALUE_Y(y), VALUE_SCALE, true);
        return;
    }

    char profile[12];
    snprintf(profile, sizeof(profile), "%d", s->profile);
    draw_header("BT", y, profile, false);

    const char *state = s->output == STATUS_OUTPUT_BT_LINKED ? "LINKED"
                        : s->output == STATUS_OUTPUT_BT_PAIR ? "PAIR"
                                                             : "SEARCH";
    draw_text_centered_scaled(state, VALUE_Y(y), VALUE_SCALE, true);
}

static void draw_battery(const struct central_status *s) {
    draw_battery_block(s->battery, s->charging);

    char text[8];
    if (s->peripheral_battery > 0) {
        snprintf(text, sizeof(text), "L %u%%", s->peripheral_battery);
    } else {
        strcpy(text, "L --");
    }
    // Under the 18 px digits
    draw_text_centered_scaled(text, VALUE_Y(BATTERY_Y) + 20, VALUE_SCALE, true);
}

static void draw_layer(const struct central_status *s, int y) {
    draw_header("LAYER", y, NULL, false);

    char text[12];
    // Kept off the edges: HSCROLL would fill the width exactly
    layout_layer_text(s, VALUE_SCALE, SCREEN_W - 6, text, sizeof(text));
    draw_text_centered_scaled(text, VALUE_Y(y), VALUE_SCALE, true);
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
        int cy = VALUE_Y(y) + (i / 2) * (MOD_CELL_H + MOD_CELL_GAP);
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
    draw_battery(status);
    draw_output(status, LINK_Y);
    draw_layer(status, THIRD_Y);
    draw_mods(status, FOURTH_Y);
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
    int print_y = VALUE_Y(y);
    draw_glyph_scaled(print, PRINT_X, print_y, PRINT_SCALE, true);

    int bar_y = print_y + print->h * PRINT_SCALE + 2;
    int text_y = bar_y + BAR_HEIGHT + 3;

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
    draw_battery_block(status->battery, status->charging);

    draw_header("LINK", LINK_Y, NULL, false);
    draw_text_centered_scaled(status->linked ? "OK" : "LOST", VALUE_Y(LINK_Y), VALUE_SCALE, true);

    if (status->touchid) {
        draw_touchid(status, THIRD_Y);
    }
}
