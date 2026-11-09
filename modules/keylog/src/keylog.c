/*
 * Key logger: streams key positions, keycodes and layer changes to the host over
 * Raw HID (zzeneg/zmk-raw-hid), so tools/keylog can record how the keyboard is
 * really used: which physical key, which layer, how long it was held and what
 * the hold-taps decided. Runs on the central (right) half, which sees both
 * halves' positions.
 *
 * Nothing is sent unless the host asks: the host sends a start command and has
 * to renew it every few seconds, so the keyboard goes quiet when the logger app
 * isn't running (or another computer is connected).
 *
 * Report (CONFIG_RAW_HID_REPORT_SIZE = 32 bytes):
 *   [0] KEYLOG_MAGIC  [1] sequence number  then 3 records of 10 bytes:
 *   type u8, flags u8, a u8, b u8, c u16 LE, time u32 LE (ms since boot)
 *     POSITION  flags bit0 pressed, a position, b source (255 = this half)
 *     KEYCODE   flags bit0 pressed, a usage page, b modifiers, c keycode
 *     LAYER     flags bit0 active, a layer, b highest active layer, c layer state
 *     DROPPED   c records lost since the last one (buffer full)
 */

#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/byteorder.h>

#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/keymap.h>

#include <raw_hid/events.h>

LOG_MODULE_REGISTER(keylog, CONFIG_ZMK_LOG_LEVEL);

#define KEYLOG_MAGIC 0x4B // 'K'

#define KEYLOG_CMD_STOP 0x00
#define KEYLOG_CMD_START 0x01

enum keylog_type {
    KEYLOG_POSITION = 1,
    KEYLOG_KEYCODE = 2,
    KEYLOG_LAYER = 3,
    KEYLOG_DROPPED = 4,
};

#define RECORD_SIZE 10
#define HEADER_SIZE 2
#define RECORDS_PER_REPORT ((CONFIG_RAW_HID_REPORT_SIZE - HEADER_SIZE) / RECORD_SIZE)

BUILD_ASSERT(RECORDS_PER_REPORT >= 1, "Raw HID report too small for a key log record");

struct record {
    uint8_t type;
    uint8_t flags;
    uint8_t a;
    uint8_t b;
    uint16_t c;
    uint32_t time;
};

static struct record ring[CONFIG_KEYBALL61_KEYLOG_BUFFER];
static size_t ring_head, ring_len;
static uint16_t dropped;
static struct k_spinlock lock;

static uint8_t report[CONFIG_RAW_HID_REPORT_SIZE];
static uint8_t seq;

static int64_t lease_until;

static bool streaming(void) { return k_uptime_get() < lease_until; }

static void flush_work_cb(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(flush_work, flush_work_cb);

static void push(struct record rec) {
    if (!streaming()) {
        return;
    }

    size_t pending;
    K_SPINLOCK(&lock) {
        if (ring_len == ARRAY_SIZE(ring)) {
            dropped++;
        } else {
            ring[(ring_head + ring_len) % ARRAY_SIZE(ring)] = rec;
            ring_len++;
        }
        pending = ring_len;
    }

    // A full report goes out now; a partial one waits briefly for company
    k_work_schedule(&flush_work, pending >= RECORDS_PER_REPORT
                                     ? K_NO_WAIT
                                     : K_MSEC(CONFIG_KEYBALL61_KEYLOG_FLUSH_MS));
}

static void put_record(uint8_t *out, const struct record *rec) {
    out[0] = rec->type;
    out[1] = rec->flags;
    out[2] = rec->a;
    out[3] = rec->b;
    sys_put_le16(rec->c, &out[4]);
    sys_put_le32(rec->time, &out[6]);
}

static void flush_work_cb(struct k_work *work) {
    for (;;) {
        size_t n = 0;

        memset(report, 0, sizeof(report));
        report[0] = KEYLOG_MAGIC;
        report[1] = seq++;

        K_SPINLOCK(&lock) {
            if (dropped && ring_len < ARRAY_SIZE(ring)) {
                // Report the loss in order, where it happened
                put_record(&report[HEADER_SIZE], &(struct record){.type = KEYLOG_DROPPED,
                                                                  .c = dropped,
                                                                  .time = k_uptime_get_32()});
                dropped = 0;
                n++;
            }
            while (n < RECORDS_PER_REPORT && ring_len) {
                put_record(&report[HEADER_SIZE + n * RECORD_SIZE], &ring[ring_head]);
                ring_head = (ring_head + 1) % ARRAY_SIZE(ring);
                ring_len--;
                n++;
            }
        }

        if (n == 0) {
            seq--;
            return;
        }

        if (streaming()) {
            raise_raw_hid_sent_event(
                (struct raw_hid_sent_event){.data = report, .length = sizeof(report)});
        }
    }
}

static int keylog_listener(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *pos = as_zmk_position_state_changed(eh);
    if (pos) {
        push((struct record){.type = KEYLOG_POSITION,
                             .flags = pos->state,
                             .a = (uint8_t)pos->position,
                             .b = pos->source,
                             .time = (uint32_t)pos->timestamp});
        return ZMK_EV_EVENT_BUBBLE;
    }

    const struct zmk_keycode_state_changed *kc = as_zmk_keycode_state_changed(eh);
    if (kc) {
        push((struct record){.type = KEYLOG_KEYCODE,
                             .flags = kc->state,
                             .a = (uint8_t)kc->usage_page,
                             .b = kc->implicit_modifiers | kc->explicit_modifiers,
                             .c = (uint16_t)kc->keycode,
                             .time = (uint32_t)kc->timestamp});
        return ZMK_EV_EVENT_BUBBLE;
    }

    const struct zmk_layer_state_changed *layer = as_zmk_layer_state_changed(eh);
    if (layer) {
        push((struct record){.type = KEYLOG_LAYER,
                             .flags = layer->state,
                             .a = layer->layer,
                             .b = zmk_keymap_highest_layer_active(),
                             .c = (uint16_t)zmk_keymap_layer_state(),
                             .time = (uint32_t)layer->timestamp});
        return ZMK_EV_EVENT_BUBBLE;
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(keylog, keylog_listener);
ZMK_SUBSCRIPTION(keylog, zmk_position_state_changed);
ZMK_SUBSCRIPTION(keylog, zmk_keycode_state_changed);
ZMK_SUBSCRIPTION(keylog, zmk_layer_state_changed);

static int keylog_command_listener(const zmk_event_t *eh) {
    const struct raw_hid_received_event *ev = as_raw_hid_received_event(eh);
    if (!ev || ev->length < 2 || ev->data[0] != KEYLOG_MAGIC) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    switch (ev->data[1]) {
    case KEYLOG_CMD_START:
        if (!streaming()) {
            LOG_INF("Key log streaming on");
        }
        lease_until = k_uptime_get() + CONFIG_KEYBALL61_KEYLOG_LEASE_MS;
        break;
    case KEYLOG_CMD_STOP:
        LOG_INF("Key log streaming off");
        lease_until = 0;
        K_SPINLOCK(&lock) {
            ring_len = 0;
            dropped = 0;
        }
        break;
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(keylog_command, keylog_command_listener);
ZMK_SUBSCRIPTION(keylog_command, raw_hid_received_event);
