# Repository instructions

## Firmware flashing

- After producing or downloading a new Keyball61 UF2 artifact for installation, use the repo skill at `.agents/skills/keyball-firmware-flash/SKILL.md` and `scripts/flash-keyball.py`. Do not use Finder or an ad hoc copy command.
- Default to an attached backend PTY and mirror every live helper prompt and completion in chat. Do not try to attach that PTY with `open_in_codex`; current sessions can report `queued` while leaving the visible integrated terminal blank.
- If the user explicitly requires the visible Codex integrated terminal, provide the exact paste-ready command for them to run there, then follow its output with the app terminal reader when available. Never open a separate Terminal.app/iTerm window or background the process.
- Flash only the requested or changed half. Do not flash `settings_reset` as part of a normal firmware update.
- A build, artifact download, or started copy is not a completed flash. Report the helper's source hash and checked transfer result, then verify physical keyboard behavior separately.
