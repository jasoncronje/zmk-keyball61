/*
 * What each half shows, gathered by central.c / peripheral.c and drawn by the
 * layout for this display: layout_oled.c (128x32 OLED) or layout_nice_view.c
 * (160x68 nice!view). Layouts only draw with draw.h, so scripts/preview.py can
 * build them on the host.
 */

#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <keyball61/touchid_power.h>

// Held modifiers, either side's key
#define STATUS_MOD_CTL (1U << 0)
#define STATUS_MOD_OPT (1U << 1)
#define STATUS_MOD_CMD (1U << 2)
#define STATUS_MOD_SFT (1U << 3)

enum status_output {
    STATUS_OUTPUT_USB,
    STATUS_OUTPUT_BT_LINKED,
    STATUS_OUTPUT_BT_PAIR,
    STATUS_OUTPUT_BT_SEARCH,
};

struct central_status {
    uint8_t battery;
    bool charging;
    // The left half's battery; 0 until it first reports
    uint8_t peripheral_battery;
    enum status_output output;
    // 1-based BLE profile
    int profile;
    // NULL or empty when the layer has no name
    const char *layer_name;
    uint8_t layer_index;
    uint8_t mods;
};

struct peripheral_status {
    uint8_t battery;
    bool charging;
    bool linked;
    // false when the build has no Touch ID power control
    bool touchid;
    enum keyball61_touchid_mode touchid_mode;
    bool touchid_on;
    // 0 when no off countdown is running
    uint32_t touchid_remaining_ms;
    uint32_t touchid_off_delay_ms;
};

// Redraws through the Touch ID off countdown (peripheral.c); the OLED's
// countdown bar is this many pixels wide, one per redraw. 60 keeps the
// nice!view's minutes left within 15 s of the real time.
#ifdef CONFIG_KEYBALL61_STATUS_SCREEN_NICE_VIEW
#define LAYOUT_TOUCHID_STEPS 60
#else
#define LAYOUT_TOUCHID_STEPS 30
#endif

void layout_central(const struct central_status *status);
void layout_peripheral(const struct peripheral_status *status);

// The layer's name as shown at this text scale within max_width: uppercased,
// FUNCTION as FN and HSCROLL as HSCRL when too wide, anything else cut to fit;
// its number if unnamed
void layout_layer_text(const struct central_status *status, int scale, int max_width, char *text,
                       size_t size);
