# Agent guide

ZMK config for the Keyball61: split, two nice!nano v2, trackball on the right half. `README.md` covers features and hardware. This file holds only what the code doesn't tell you.

## Which build to flash

`build.yaml` builds three shields. Find out which one the user's keyboard runs before picking artifacts; never guess.

| Shield | Hardware | Left artifact | Right artifact |
|---|---|---|---|
| `keyball61` | Bought PCB, OLEDs | `keyball61_left nice_oled-nice_nano_v2-zmk.uf2` | `keyball61_right nice_oled-nice_nano_v2-zmk.uf2` |
| `keyball61_nv` | Bought PCB, nice!views | `keyball61_nv_left nice_view-nice_nano_v2-zmk.uf2` | `keyball61_nv_right nice_view-nice_nano_v2-zmk.uf2` |
| `keyball61_ble` | Open-source PCB, nice!views | `keyball61_ble_left nice_view-nice_nano_v2-zmk.uf2` | `keyball61_ble_right nice_view-nice_nano_v2-zmk.uf2` |

If the user runs the key logger (`tools/keylog`), the right half needs the `-keylog` artifact instead (`keyball61_right-keylog-…` or `keyball61_nv_right-keylog-…`), or logging stops.

## What is shared between shields

- Keymap: one file, `config/keyball61.keymap`. The `_nv` and `_ble` keymaps only include it.
- `.conf` files are per shield and not shared. Edit the files of the shield the keyboard runs (`config/<shield>.conf`, `config/boards/shields/<shield>/*.conf`); a change in another shield's file does nothing on that keyboard. Mirror a change to the other shields when it applies to them.
- Trackball, auto-mouse and scroll setup is in two right overlays that must stay in step: `keyball61/keyball61_right.overlay` and `keyball61_ble/keyball61_ble_right.overlay` (`_nv` includes the `_ble` one).
- Those overlays use layers by number (MOUSE 3, SCROLL 4, HSCROLL 5). Update them if the keymap's layer order changes.
- A key's MOUSE-layer binding only runs if its position is in `excluded-positions` in both overlays. Otherwise auto-mouse sees the press first, drops the layer, and the key resolves on DEFAULT.

## Build, push, flash

- There is no local build. Push, and GitHub Actions builds every shield in 2 to 7 minutes: `gh run list --commit <sha>`, `gh run watch <id> --exit-status`, `gh run download <id> -D <dir>`. Artifact names contain spaces, so quote them.
- A push that touches `config/` makes the keymap-drawer bot push a `[Draw]` commit about 30 s later. Run `git pull --rebase` before the next push.
- Flash by following `.agents/skills/keyball-firmware-flash/SKILL.md`. Never use Finder or `cp`.
- The right half is the central and holds the keymap. Keymap, behavior, trackball and host Bluetooth changes need the right half only. Flash the left only for what it runs itself: its screen, Touch ID power, the split link.
- Never flash `settings_reset` unless asked.
- A passed build or a checked transfer does not prove the change works. Ask the user to test on the keyboard, and wait for the answer before calling it done.

## Working on it

- Screen changes: render them with `python3 modules/status-screen/scripts/preview.py <dir>` and show the PNGs (Markdown images, absolute paths) before building.
- Tap, hold and double-tap timings: read the key log first (`python3 tools/keylog/analyze.py --days 7`). Leave values that were tried and rejected in a comment next to the setting.
- Firmware misbehaves and the cause isn't in the code: get logs from the keyboard, don't guess from the Mac. Build the affected half with the `zmk-usb-logging` snippet and ZMK Studio off, read `/dev/cu.usbmodem*` at 115200, then flash the normal build back.
- Bluetooth timing on macOS: check what the host applied with `/usr/bin/log show --last 10m --predicate 'process == "bluetoothd" AND eventMessage CONTAINS[c] "parameters"'`, not by feel. Plain `log` is a zsh builtin and prints nothing.
- Soldering or probing: name the pad by the label printed on the PCB and where it sits. The PCB prints AVR names (table in `README.md`), so `pm1` or `P0.06` alone means nothing to the user.
- Tests: `python3 -m unittest discover -s tests`.
