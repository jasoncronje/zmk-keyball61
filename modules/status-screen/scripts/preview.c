// Host build of the layouts for scripts/preview.py: prints each sample state's
// frame as rows of '#' and '.', separated by "= <name>" lines

#include <stdio.h>

#include "draw.h"
#include "layout.h"

static void print_frame(const char *name) {
    printf("= %s\n", name);
    for (int y = 0; y < SCREEN_H; y++) {
        for (int x = 0; x < SCREEN_W; x++) {
            putchar(draw_get(x, y) ? '#' : '.');
        }
        putchar('\n');
    }
}

static void central(const char *name, struct central_status status) {
    draw_clear();
    layout_central(&status);
    print_frame(name);
}

static void peripheral(const char *name, struct peripheral_status status) {
    draw_clear();
    layout_peripheral(&status);
    print_frame(name);
}

int main(void) {
    central("right-typing", (struct central_status){
                                .battery = 87,
                                .peripheral_battery = 92,
                                .output = STATUS_OUTPUT_BT_LINKED,
                                .profile = 1,
                                .layer_name = "MAIN",
                                .mods = 0,
                            });
    central("right-mods", (struct central_status){
                              .battery = 100,
                              .charging = true,
                              .peripheral_battery = 64,
                              .output = STATUS_OUTPUT_USB,
                              .layer_name = "HSCROLL",
                              .mods = STATUS_MOD_CMD | STATUS_MOD_SFT,
                          });
    central("right-search", (struct central_status){
                                .battery = 9,
                                .peripheral_battery = 0,
                                .output = STATUS_OUTPUT_BT_SEARCH,
                                .profile = 2,
                                .layer_name = "FUNCTION",
                                .mods = STATUS_MOD_CTL | STATUS_MOD_OPT,
                            });

    const uint32_t delay = 870 * 1000;
    peripheral("left-countdown", (struct peripheral_status){
                                     .battery = 92,
                                     .linked = true,
                                     .touchid = true,
                                     .touchid_mode = KEYBALL61_TOUCHID_AUTO,
                                     .touchid_on = true,
                                     .touchid_remaining_ms = 9 * 60 * 1000,
                                     .touchid_off_delay_ms = delay,
                                 });
    peripheral("left-always-on", (struct peripheral_status){
                                     .battery = 100,
                                     .charging = true,
                                     .linked = true,
                                     .touchid = true,
                                     .touchid_mode = KEYBALL61_TOUCHID_ON,
                                     .touchid_on = true,
                                     .touchid_off_delay_ms = delay,
                                 });
    peripheral("left-asleep", (struct peripheral_status){
                                  .battery = 41,
                                  .linked = false,
                                  .touchid = true,
                                  .touchid_mode = KEYBALL61_TOUCHID_AUTO,
                                  .touchid_on = false,
                                  .touchid_off_delay_ms = delay,
                              });
    return 0;
}
