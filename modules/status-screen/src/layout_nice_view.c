/*
 * The 160x68 nice!view, read in portrait (68x160) in labelled blocks: 7 px
 * headers, with values in the 5 px font at twice the size. Both halves start
 * with the same battery block, and the blocks below it line up across the
 * halves.
 *
 * Right half:
 *   BAT           this half's battery, big; a big bolt while charging
 *   BT n / USB    LINKED, SEARCH or PAIR / WIRED
 *   LAYER         highest active layer's name
 *   MODS          2x2 grid of the Mac modifier symbols, a cell lit while held
 *
 * Left half:
 *   BAT           this half's battery, big; a big bolt while charging
 *   LINK          OK or LOST
 *   LAYER         the right half's layer, -- until it arrives
 *   TOUCH ID      ON or OFF when forced; in auto, the minutes left before it
 *                 switches off, READY or ASLEEP
 */

#include <stdio.h>
#include <string.h>

#include <zephyr/sys/util.h>

#include "draw.h"
#include "layout.h"

// Values are the 5 px font at this scale
#define VALUE_SCALE 2

// Each block's value starts 2 px below its header
#define VALUE_Y(y) ((y) + HEADER_H + 2)

// Block tops, matching across the halves: the battery block is its header and
// the 18 px digits, each other block its header and a 10 px value, then 4 px
#define BATTERY_Y 0
#define SECOND_Y (VALUE_Y(BATTERY_Y) + 18 + 4)
#define THIRD_Y (VALUE_Y(SECOND_Y) + 10 + 4)
#define FOURTH_Y (VALUE_Y(THIRD_Y) + 10 + 4)

// A big bolt instead of the level while charging
static void draw_battery(uint8_t level, bool charging) {
    draw_header("BAT", BATTERY_Y, NULL, false);
    if (charging) {
        draw_glyph_scaled(&icon_bolt_big, (SCREEN_W - icon_bolt_big.w * 2) / 2,
                          VALUE_Y(BATTERY_Y), 2, true);
    } else {
        draw_big_percent_scaled(level, VALUE_Y(BATTERY_Y), 2);
    }
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

// NULL name: not known yet
static void draw_layer(const char *name, uint8_t index, int y) {
    draw_header("LAYER", y, NULL, false);

    char text[12] = "--";
    if (name != NULL) {
        // Kept off the edges: HSCROLL would fill the width exactly
        layout_layer_text(name, index, VALUE_SCALE, SCREEN_W - 6, text, sizeof(text));
    }
    draw_text_centered_scaled(text, VALUE_Y(y), VALUE_SCALE, true);
}

// The grid fills the rest of the screen
#define MOD_CELL_GAP 2
#define MOD_CELL_W ((SCREEN_W - MOD_CELL_GAP) / 2)
#define MOD_CELL_H ((SCREEN_H - VALUE_Y(FOURTH_Y) - MOD_CELL_GAP) / 2)

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
    draw_battery(status->battery, status->charging);
    draw_output(status, SECOND_Y);
    // This half always knows its layer: "" shows an unnamed layer's index
    draw_layer(status->layer_name ? status->layer_name : "", status->layer_index, THIRD_Y);
    draw_mods(status, FOURTH_Y);
}

// The mode when it's forced on or off; in auto, the minutes left before it
// switches off, READY, or ASLEEP once off
static void draw_touchid(const struct peripheral_status *s, int y) {
    draw_header("TOUCH ID", y, NULL, false);

    char text[8];
    if (s->touchid_mode == KEYBALL61_TOUCHID_ON) {
        strcpy(text, "ON");
    } else if (s->touchid_mode == KEYBALL61_TOUCHID_OFF) {
        strcpy(text, "OFF");
    } else if (!s->touchid_on) {
        strcpy(text, "ASLEEP");
    } else if (s->touchid_remaining_ms > 0) {
        snprintf(text, sizeof(text), "%uM", DIV_ROUND_UP(s->touchid_remaining_ms, 60000U));
    } else {
        strcpy(text, "READY");
    }
    draw_text_centered_scaled(text, VALUE_Y(y), VALUE_SCALE, true);
}

void layout_peripheral(const struct peripheral_status *status) {
    draw_battery(status->battery, status->charging);

    draw_header("LINK", SECOND_Y, NULL, false);
    draw_text_centered_scaled(status->linked ? "OK" : "LOST", VALUE_Y(SECOND_Y), VALUE_SCALE,
                              true);

    // The right half sends an unnamed layer's index as its name
    draw_layer(status->layer_name, 0, THIRD_Y);

    if (status->touchid) {
        draw_touchid(status, FOURTH_Y);
    }
}
