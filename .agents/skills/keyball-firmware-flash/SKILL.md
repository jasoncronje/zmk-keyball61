---
name: keyball-firmware-flash
description: Flash newly built or downloaded Keyball61 ZMK UF2 firmware to one or both nice!nano halves. Use after producing firmware artifacts, when asked to flash/update/recover a half, or when a Keyball61 firmware zip must be installed without Finder.
---

# Keyball61 firmware flashing

Use the repository helper instead of Finder or ad hoc `cp` commands.

1. Resolve the repository root with `git rev-parse --show-toplevel`.
2. Identify the exact left/right UF2 artifacts. Never infer a half from build intent alone. The helper accepts individual UF2s, a ZMK `firmware.zip`, or a directory and rejects ambiguous names and `settings_reset`.
3. Validate the plan first when artifact selection is uncertain:

   ```sh
   ./scripts/flash-keyball.py --check /absolute/path/to/firmware.zip
   ```

4. Choose the execution path:

   - Default: start the helper in an attached backend PTY in the current Codex task. Keep it foregrounded and mirror every plug/reset/disconnect prompt and completion in chat as it appears. Do not call `open_in_codex` for this PTY: backend PTY sessions currently return `queued` without attaching to the visible integrated terminal.
   - If the user explicitly requires the visible integrated terminal, do not start a backend copy. Give them the exact paste-ready command and ask them to run it in Codex's terminal. Then follow its output with the app terminal reader when available.

   Never launch Terminal.app/iTerm, background the helper, or use `osascript`.

   ```sh
   ./scripts/flash-keyball.py /absolute/path/to/firmware.zip
   ./scripts/flash-keyball.py --left /absolute/path/to/left.uf2
   ./scripts/flash-keyball.py --right /absolute/path/to/right.uf2
   ./scripts/flash-keyball.py --left /absolute/path/to/left.uf2 --right /absolute/path/to/right.uf2
   ```

5. Keep the backend PTY attached until the helper exits. Poll the same session and relay state changes promptly; do not leave the user guessing while it waits. The helper prompts for each physical half, waits for `NICENANO`, validates the UF2, copies it, checks the transfer, and signals when the half can be disconnected.
6. Report each source SHA-256 and transfer result. A checked transfer is not proof of runtime behavior; ask the user to verify keys, split connection, and pointer movement after reconnecting.

Only flash the requested/changed half. Never flash `settings_reset` unless the user explicitly requests a separate reset procedure; this helper intentionally refuses it.
