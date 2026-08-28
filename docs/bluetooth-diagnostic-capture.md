# Bluetooth diagnostic capture

This diagnostic firmware preserves the rollback behavior: PMW3610 CPI 400,
125 Hz sensor polling, 16 ms BLE mouse report coalescing, and the existing BLE
connection settings. It adds fixed-RAM event capture on the right half. Nothing
is formatted, logged, or written to flash while reproducing the problem.

This is minimally perturbing, not literally zero-overhead instrumentation. In
particular, each mouse notification has a small completion callback on the
system workqueue, and valid split key notifications update RAM counters.

## Capture

1. Flash only the right-half diagnostic firmware. Leave the left half on the
   rollback firmware.
2. Keep USB disconnected. Use Bluetooth until the lag or wake/reconnect fault
   occurs.
3. Stop moving the ball. Do not power-cycle either half; the trace is RAM-only.
4. Quit ZMK Studio.
5. Connect the right half by USB.
6. Find the CDC port:

   ```sh
   ls /dev/cu.usbmodem*
   ```

7. Capture the raw CSV dump:

   ```sh
   /usr/bin/cu -l /dev/cu.usbmodemXXXX -s 115200 | tee keyball-diag.csv
   ```

   Replace the port name. Wait for `KEYBALL_DIAG_END`, press Return, then type
   `~.` to exit `cu`. USB attachment freezes the trace; opening the port asserts
   DTR and starts the dump.

Accept a trace only when it has one `KEYBALL_DIAG_BEGIN,2`, one
`KEYBALL_DIAG_END`, no `LOST`/`STATE_LOST` rows, and the retained row counts
match `SUMMARY` and `STATE_SUMMARY`. If the capture is partial, close and reopen
the CDC port. The frozen RAM trace is emitted again on every DTR close/reopen.
It is cleared only after USB disconnects.

The hot ring contains the final 1,024 timing events. Routine HOG returns,
workqueue runs, and GATT API returns are aggregates only; error or slow cases
are kept as rows. A separate 128-row state ring retains host, activity, and
split transitions so a busy pointer trace cannot erase the wake chronology.
`HOST_STATE`, `SPLIT_STATE`, `SPLIT_LINK_STATE`, and `SPLIT_RX_STATE` retain the
final link state.

## Event fields

All `EVENT` rows use:

```text
EVENT,sequence,timestamp_us,type,name,a,b,c,d
```

Key payloads:

- `input`: processed X, Y, vertical scroll, horizontal scroll.
- `hog_result`: enqueue result, host connected flag, call duration in us.
- `work`: scheduled due timestamp, workqueue lateness in us.
- `notify_return`: notification ID, GATT return code, API duration in us,
  packed X/Y delta.
- `notify_complete`: notification ID, controller completion latency in us,
  outstanding notification count, packed X/Y delta.
- `host_params`: BLE interval in 1.25 ms units, slave latency, supervision
  timeout in 10 ms units, connection role.
- `split_params`: the left/right BLE link interval in 1.25 ms units, slave
  latency, supervision timeout in 10 ms units, and connection role. It is
  recorded at connection and on every later parameter update.
- Split rows record scan, service discovery, connection, disconnection, and
  security transitions. `split_subscribe` is the immediate request result;
  `split_subscribe_complete` is the actual CCC write response. `split_ready`
  means required handles were found and subscription requests were accepted.
  The first valid `split_rx` establishes functional left-half readiness,
  separately exposed as `SPLIT_RX_STATE,functional_ready`. Later `split_rx`
  rows are sampled every 32 notifications or retained for a gap of at least
  100 ms; the full count and maximum gap remain in `SPLIT_RX_STATE`.

For notification rows, `d` packs the signed deltas: low 16 bits are X and high
16 bits are Y. Interpret the CSV integer as a 32-bit unsigned value before
sign-extending each 16-bit half.

The GATT completion callback proves that Zephyr received controller transmit
completion. It does not prove when macOS consumed or rendered the HID report.
