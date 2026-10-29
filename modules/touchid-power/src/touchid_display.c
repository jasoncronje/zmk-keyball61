/*
 * Touch ID icon: a fingerprint at the bottom of the left OLED while the Touch ID
 * board is powered. Drawn through zmk-nice-oled's peripheral extras hook, which
 * runs on the display work queue as part of every peripheral screen redraw.
 */

#include <zephyr/kernel.h>

#include <lvgl.h>

#include <zmk/display.h>

#include "touchid_power.h"

// From zmk-nice-oled's widgets/screen_peripheral.h, which isn't on our include path
void nice_oled_peripheral_redraw(void);

#define ICON_X 16
#define ICON_Y CONFIG_KEYBALL61_TOUCHID_ICON_CENTER_Y

static void draw_arc(lv_obj_t *canvas, const lv_draw_arc_dsc_t *dsc, uint16_t radius,
                     uint16_t start, uint16_t end) {
    lv_canvas_draw_arc(canvas, ICON_X, ICON_Y, radius, start, end, dsc);
}

void nice_oled_draw_peripheral_extras(lv_obj_t *canvas) {
    if (!keyball61_touchid_is_on()) {
        return;
    }

    lv_draw_arc_dsc_t dsc;
    lv_draw_arc_dsc_init(&dsc);
    dsc.color = IS_ENABLED(CONFIG_NICE_OLED_WIDGET_INVERTED) ? lv_color_white() : lv_color_black();
    dsc.width = 2;

    // Outer ring, then ridges with breaks at different angles so it reads as a print
    // (LVGL angles: 0 = right, clockwise; start > end wraps through 0)
    draw_arc(canvas, &dsc, 14, 0, 359);
    draw_arc(canvas, &dsc, 10, 200, 160);
    draw_arc(canvas, &dsc, 7, 300, 240);
    draw_arc(canvas, &dsc, 4, 120, 60);
    draw_arc(canvas, &dsc, 2, 0, 359);
}

static void redraw_work_cb(struct k_work *work) { nice_oled_peripheral_redraw(); }

static K_WORK_DEFINE(redraw_work, redraw_work_cb);

void keyball61_touchid_display_update(void) {
    k_work_submit_to_queue(zmk_display_work_q(), &redraw_work);
}
