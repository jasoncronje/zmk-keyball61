/*
 * The 128x32 OLED, read in portrait (32x128) in labelled blocks.
 *
 * Right half:
 *   BAT  [bolt]   this half's battery, big, then the left half's
 *   BT n / USB    LINKED, SEARCH or PAIR / WIRED
 *   LAYER         highest active layer's name
 *   MODS          CTL OPT CMD SFT, lit while held
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

static const struct {
    const char *label;
    const struct glyph *icon;
    uint8_t mods;
} mod_rows[] = {
    {"CTL", &icon_ctl, STATUS_MOD_CTL},
    {"OPT", &icon_opt, STATUS_MOD_OPT},
    {"CMD", &icon_cmd, STATUS_MOD_CMD},
    {"SFT", &icon_sft, STATUS_MOD_SFT},
};

static void draw_battery(const struct central_status *s) {
    draw_header("BAT", 0, NULL, s->charging);
    draw_big_percent(s->battery, 11);

    char text[8];
    if (s->peripheral_battery > 0) {
        snprintf(text, sizeof(text), "L %u%%", s->peripheral_battery);
    } else {
        strcpy(text, "L --");
    }
    draw_text_centered(text, 22, true);
}

static void draw_output(const struct central_status *s) {
    if (s->output == STATUS_OUTPUT_USB) {
        draw_header("USB", 28, NULL, false);
        draw_text_centered("WIRED", 40, true);
        return;
    }

    char profile[12];
    snprintf(profile, sizeof(profile), "%d", s->profile);
    draw_header("BT", 28, profile, false);

    if (s->output == STATUS_OUTPUT_BT_LINKED) {
        draw_text_centered("LINKED", 40, true);
    } else if (s->output == STATUS_OUTPUT_BT_PAIR) {
        draw_text_centered("PAIR", 40, true);
    } else {
        draw_text_centered("SEARCH", 40, true);
    }
}

static void draw_layer(const struct central_status *s) {
    draw_header("LAYER", 52, NULL, false);

    char text[12];
    layout_layer_text(s, 1, SCREEN_W, text, sizeof(text));
    draw_text_centered(text, 64, true);
}

static void draw_mods(const struct central_status *s) {
    draw_header("MODS", 76, NULL, false);

    for (size_t i = 0; i < ARRAY_SIZE(mod_rows); i++) {
        int y = 88 + i * 10;
        bool held = s->mods & mod_rows[i].mods;

        if (held) {
            draw_rect(0, y - 1, SCREEN_W, 9, true);
        }
        draw_glyph(mod_rows[i].icon, 2, y - 1, !held);
        draw_text(mod_rows[i].label, 15, y + 1, !held);
    }
}

void layout_central(const struct central_status *status) {
    draw_battery(status);
    draw_output(status);
    draw_layer(status);
    draw_mods(status);
}

#define PRINT_X 1
#define PRINT_Y 68

#define BAR_Y (PRINT_Y + 30)
#define BAR_HEIGHT 2

// Always-on dashes: 2 px on, 2 px off, across the bar's width
#define DASH_WIDTH 2
#define DASH_PITCH 4

static void draw_touchid(const struct peripheral_status *s) {
    static const char *const mode_labels[] = {
        [KEYBALL61_TOUCHID_AUTO] = "A",
        [KEYBALL61_TOUCHID_ON] = "ON",
        [KEYBALL61_TOUCHID_OFF] = "OFF",
    };
    draw_header("TID", 52, mode_labels[s->touchid_mode], false);

    draw_glyph(s->touchid_on ? &icon_fingerprint_on : &icon_fingerprint_off, PRINT_X, PRINT_Y,
               true);

    if (s->touchid_mode == KEYBALL61_TOUCHID_ON) {
        for (int x = 0; x < LAYOUT_TOUCHID_BAR_WIDTH; x += DASH_PITCH) {
            draw_rect(PRINT_X + x, BAR_Y, DASH_WIDTH, BAR_HEIGHT, true);
        }
    } else if (s->touchid_on && s->touchid_remaining_ms > 0) {
        int width = DIV_ROUND_UP((uint64_t)LAYOUT_TOUCHID_BAR_WIDTH * s->touchid_remaining_ms,
                                 s->touchid_off_delay_ms);
        width = CLAMP(width, 1, LAYOUT_TOUCHID_BAR_WIDTH);
        draw_rect(PRINT_X + (LAYOUT_TOUCHID_BAR_WIDTH - width) / 2, BAR_Y, width, BAR_HEIGHT,
                  true);

        char minutes[8];
        snprintf(minutes, sizeof(minutes), "%uM", DIV_ROUND_UP(s->touchid_remaining_ms, 60000U));
        draw_text_centered(minutes, 108, true);
        return;
    }

    draw_text_centered(s->touchid_on ? "READY" : "ASLEEP", 108, true);
}

void layout_peripheral(const struct peripheral_status *status) {
    draw_header("BAT", 0, NULL, status->charging);
    draw_big_percent(status->battery, 12);

    draw_header("LINK", 28, NULL, false);
    draw_text_centered(status->linked ? "OK" : "LOST", 40, true);

    if (status->touchid) {
        draw_touchid(status);
    }
}
