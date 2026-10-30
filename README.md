# Keyball61 ZMK Config

A heavily customized ZMK firmware for the wireless [Keyball61](https://github.com/Yowkees/keyball), a 61-key split ortho with an integrated 34mm trackball, running over BLE and tuned for macOS. This repo is specifically for **BLE / ZMK** builds. If you're running the wired QMK variant, take a look at: [Yowkees/keyball](https://github.com/Yowkees/keyball).

> **Note:** This is my personal config, you can use as is or fork to tweak things to your liking.

## My Keymap

<details>
<summary>View keymap</summary>

<img src="keymap-drawer/keyball61.svg">

</details>

## How I Got Here

I came to the Keyball61 from a [UHK 60](https://uhk.io/uhk60). The UHK 60 sold me on split ergo and thumb-mounted trackballs, both non-negotiable now, but it was heavy, bulky, and the trackball was a bolt-on module instead of a first-class part of the keyboard. The Keyball61 is the keyboard I was actually looking for: integrated trackball, ortho-linear, wireless, light. If you aren't used to ortho-linear it can be a little frustrating to get used to, but don't give up. A few days in it suddenly clicked for me and I haven't looked back.

## Customizations

- **ZMK v0.3.0**: upgraded from v0.2 for module support and input processors.
- **PMW3610 trackball driver**: [kumamuk-git/zmk-pmw3610-driver](https://github.com/kumamuk-git/zmk-pmw3610-driver) with SPI. This allowed me to switch the trackball to vertical/side scroll on certain layers.
- **Native auto-mouse**: `zip_temp_layer` input processor instead of driver-level automouse. Excludes click positions, respects typing idle.
- **OLEDs**: [zmk-nice-oled](https://github.com/mctechnology17/zmk-nice-oled) module, vertical layout, battery % and sleep. I plan to work on this more soon.
- **BLE tuned**: optimized for Mac OS bluetooth connectivity and fixing latency issues. 

## Hardware Mods

I've printed custom cases, combined MX switch plates with bottom-access screws, and protective covers for storage and travel. Parts, print downloads, and assembly notes are in the [build sheet](docs/build-sheet.md).

![My Keyball61 build](docs/MyBuild.jpeg)

## Building Firmware

Firmware builds automatically via GitHub Actions on pushes and pull requests. Renovate branches build through their pull requests to avoid duplicate push builds. A separate [keymap-drawer](https://github.com/caksoylar/keymap-drawer) workflow regenerates keymap images on relevant pushes. Day-to-day keymap edits are made with [keymap-editor](https://nickcoutsos.github.io/keymap-editor/) rather than ZMK Studio.

## Dependency Updates

[Renovate](https://github.com/apps/renovate) checks for updates on Mondays between midnight and 7 a.m. in `America/Los_Angeles`. The hosted bot runs within that window, not at an exact time. It opens at most three update PRs at once and never merges them automatically.

The rules in `renovate.json` cover GitHub Actions and the annotated dependencies in `config/west.yml`:

- ZMK follows stable version tags.
- The PMW3610 driver follows `kumamuk-git/zmk-pmw3610-driver`'s `main` branch, stored as an exact commit. The initial pin, `5e04553ab803d24405bd45621a41310ea3050e59`, matches the checkout recorded in [successful build 40976203775](https://github.com/jasoncronje/zmk-keyball61/actions/runs/40976203775).
- The OLED module follows this fork's `keyball61/peripheral-extras-hook` branch, preserving its custom hooks. It does not follow upstream or the fork's `main` branch.

To activate, merge this configuration into the default branch and enable the Renovate GitHub App for this repository. Once the app processes the repository, use its Dependency Dashboard to inspect updates or request a check outside the schedule. Configuration in Git alone does not activate the bot.

Before merging a firmware dependency update, inspect the upstream changes, require a successful firmware build, flash only the affected half with the helper below, and check pointer movement, scrolling, typing, Bluetooth reconnect, and affected display or Touch ID behavior. A build cannot verify physical behavior. Keep dependencies in separate PRs so regressions are easy to isolate.

The manifest rules cover its three direct projects. Dependencies imported by ZMK remain governed by ZMK's own manifest.

## Flashing Firmware

Use the interactive helper instead of dragging files in Finder. It accepts a ZMK `firmware.zip`, individual left/right UF2 files, or a directory. It validates the images, waits for each `NICENANO` bootloader volume, flashes it, checks the transfer, and tells you when to disconnect each half.

```sh
./scripts/flash-keyball.py /path/to/firmware.zip
./scripts/flash-keyball.py --right /path/to/keyball61_right-zmk.uf2
./scripts/flash-keyball.py --left /path/to/left.uf2 --right /path/to/right.uf2
```

Validate artifact selection without touching hardware:

```sh
./scripts/flash-keyball.py --check /path/to/firmware.zip
```

## Attribution

Forked originally from [tangbonze/zmk-config-Keyball61](https://github.com/tangbonze/zmk-config-Keyball61), which builds on firmware by [Amos698](https://github.com/Amos698).
