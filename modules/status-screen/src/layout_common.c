#include <stdio.h>
#include <string.h>

#include <zephyr/sys/util.h>

#include "draw.h"
#include "layout.h"

// Names too wide for the screen, as they're shown instead
static const struct {
    const char *name;
    const char *shown;
} layer_short_names[] = {
    {"FUNCTION", "FN"},
    {"HSCROLL", "HSCRL"},
};

static void copy_upper(const char *name, char *text, size_t size) {
    size_t len = 0;
    for (; name[len] != '\0' && len < size - 1; len++) {
        char c = name[len];
        text[len] = (c >= 'a' && c <= 'z') ? c - 'a' + 'A' : c;
    }
    text[len] = '\0';
}

void layout_layer_text(const char *name, uint8_t index, int scale, int max_width, char *text,
                       size_t size) {
    if (name == NULL || name[0] == '\0') {
        snprintf(text, size, "%u", index);
        return;
    }

    copy_upper(name, text, size);
    if (draw_text_width_scaled(text, scale) > max_width) {
        for (size_t i = 0; i < ARRAY_SIZE(layer_short_names); i++) {
            if (strcmp(text, layer_short_names[i].name) == 0) {
                copy_upper(layer_short_names[i].shown, text, size);
                break;
            }
        }
    }

    // Cut anything else that doesn't fit
    size_t len = strlen(text);
    while (len > 1 && draw_text_width_scaled(text, scale) > max_width) {
        text[--len] = '\0';
    }
}
