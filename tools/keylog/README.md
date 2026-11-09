# Key logger

Records how the Keyball61 is really used, to tune the keymap from data: which physical key, which layer, how long each key was held, what the hold-taps decided, and what got deleted with Backspace.

| Part | Where | What it does |
|---|---|---|
| Firmware | `modules/keylog` | On the right (central) half: streams key positions, keycodes and layer changes over Raw HID ([zzeneg/zmk-raw-hid](https://github.com/zzeneg/zmk-raw-hid)), BLE or USB |
| Mac logger | `tools/keylog/keylogd.swift` | Asks the keyboard to stream and saves every record to SQLite with the frontmost app |
| Report | `tools/keylog/analyze.py` | Markdown report from the log and `config/keyball61.keymap` |

## Use

1. Flash a keylog build of the right half: `keyball61_right-keylog-nice_nano_v2-zmk.uf2` (OLED) or `keyball61_nv_right-keylog-nice_nano_v2-zmk.uf2` (nice!view).
2. Build and run the logger:

   ```sh
   swiftc -O -o ~/.local/bin/keyball-keylogd tools/keylog/keylogd.swift
   ~/.local/bin/keyball-keylogd
   ```

3. Type normally for a few days, then:

   ```sh
   python3 tools/keylog/analyze.py --days 7
   ```

The log is `~/Library/Application Support/keyball-keylog/keylog.sqlite`.

## Privacy

- The keyboard streams only while the logger keeps renewing its start command (every 3 s, 10 s lease). Quit the logger and it stops within 10 s.
- Nothing is saved while macOS Secure Input is on (password fields, Terminal's Secure Keyboard Entry).
- Pause: `touch "$HOME/Library/Application Support/keyball-keylog/paused"`; resume by deleting the file.
- The log holds keycodes, so text can be rebuilt from it. It stays local; delete the SQLite file to wipe it.

## Limits

- Positions swallowed by a combo may be missed; the combo's keycode is still logged.
- Hold-tap outcomes are inferred: a hold is the hold modifier or layer turning on while the key is down.
- Reports lost on the radio show up as `lost reports` gaps (sequence numbers skip).
- Adding Raw HID adds a second HID service. If macOS doesn't see it after flashing, remove the keyboard in Bluetooth settings and pair it again.
