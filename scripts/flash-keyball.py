#!/usr/bin/env python3
"""Interactively flash Keyball61 ZMK UF2 firmware on macOS."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import struct
import sys
import tempfile
import time
import zipfile
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


UF2_BLOCK_SIZE = 512
UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
SIDES = ("left", "right")


class FlashError(RuntimeError):
    pass


@dataclass(frozen=True)
class Firmware:
    side: str
    path: Path
    size: int
    sha256: str
    blocks: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_uf2(path: Path) -> tuple[int, int, str]:
    if not path.is_file():
        raise FlashError(f"Firmware file not found: {path}")
    if path.suffix.lower() != ".uf2":
        raise FlashError(f"Not a .uf2 file: {path}")
    if "settings_reset" in path.name.lower():
        raise FlashError(f"Refusing settings-reset firmware: {path.name}")

    size = path.stat().st_size
    if size == 0 or size % UF2_BLOCK_SIZE:
        raise FlashError(f"Invalid UF2 size ({size} bytes): {path}")

    blocks = size // UF2_BLOCK_SIZE
    with path.open("rb") as source:
        for index in range(blocks):
            block = source.read(UF2_BLOCK_SIZE)
            start0, start1 = struct.unpack_from("<II", block, 0)
            end = struct.unpack_from("<I", block, UF2_BLOCK_SIZE - 4)[0]
            if (start0, start1, end) != (
                UF2_MAGIC_START0,
                UF2_MAGIC_START1,
                UF2_MAGIC_END,
            ):
                raise FlashError(f"Invalid UF2 magic in block {index}: {path}")
    return size, blocks, sha256_file(path)


def infer_side(name: str) -> str | None:
    lowered = name.lower()
    matches = [
        side
        for side in SIDES
        if re.search(rf"(^|[^a-z]){side}([^a-z]|$)", lowered)
    ]
    return matches[0] if len(matches) == 1 else None


def collect_uf2_files(source: Path, stack: ExitStack) -> list[Path]:
    source = source.expanduser().resolve()
    if source.is_file() and source.suffix.lower() == ".uf2":
        return [source]
    if source.is_dir():
        return sorted(path for path in source.rglob("*.uf2") if path.is_file())
    if source.is_file() and source.suffix.lower() == ".zip":
        extract_root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        try:
            with zipfile.ZipFile(source) as archive:
                safe_members = [
                    member
                    for member in archive.infolist()
                    if not member.is_dir()
                    and member.filename.lower().endswith(".uf2")
                    and not member.filename.startswith("__MACOSX/")
                    and ".." not in Path(member.filename).parts
                ]
                for member in safe_members:
                    destination = extract_root / Path(member.filename).name
                    with archive.open(member) as zipped, destination.open("wb") as output:
                        shutil.copyfileobj(zipped, output)
        except zipfile.BadZipFile as error:
            raise FlashError(f"Invalid zip archive: {source}") from error
        return sorted(extract_root.glob("*.uf2"))
    raise FlashError(f"Expected a UF2 file, firmware zip, or directory: {source}")


def resolve_firmware(
    positional: list[Path], explicit: dict[str, Path | None], stack: ExitStack
) -> list[Firmware]:
    candidates: list[tuple[str | None, Path]] = []
    if positional and any(explicit.values()):
        raise FlashError("Use positional auto-detection or --left/--right, not both")

    if positional:
        for source in positional:
            for path in collect_uf2_files(source, stack):
                if "settings_reset" not in path.name.lower():
                    candidates.append((infer_side(path.name), path))
    else:
        for side in SIDES:
            source = explicit[side]
            if source is None:
                continue
            resolved_source = source.expanduser().resolve()
            direct_uf2 = resolved_source.is_file() and resolved_source.suffix.lower() == ".uf2"
            matches = []
            for path in collect_uf2_files(source, stack):
                if "settings_reset" in path.name.lower():
                    continue
                inferred = infer_side(path.name)
                if direct_uf2 and path == resolved_source:
                    if inferred is not None and inferred != side:
                        raise FlashError(
                            f"{path.name} looks like {inferred} firmware, not {side}"
                        )
                    matches.append(path)
                elif inferred == side:
                    matches.append(path)
            if len(matches) != 1:
                raise FlashError(
                    f"Expected exactly one {side} UF2 in {source}; found {len(matches)}"
                )
            candidates.append((side, matches[0]))

    if not candidates:
        raise FlashError("No left or right firmware found")

    resolved: dict[str, Path] = {}
    for side, path in candidates:
        if side is None:
            raise FlashError(
                f"Cannot infer half from {path.name}; pass it with --left or --right"
            )
        if side in resolved:
            raise FlashError(
                f"Multiple {side} firmware files: {resolved[side].name}, {path.name}"
            )
        resolved[side] = path

    firmware: list[Firmware] = []
    for side in SIDES:
        path = resolved.get(side)
        if path is None:
            continue
        size, blocks, digest = validate_uf2(path)
        firmware.append(Firmware(side, path, size, digest, blocks))
    return firmware


def volume_matches(volume: Path, expected_name: str) -> bool:
    try:
        info = (volume / "INFO_UF2.TXT").read_text(errors="replace")
    except OSError:
        return False
    name = volume.name.upper()
    expected = expected_name.upper()
    if name != expected and not name.startswith(f"{expected} "):
        return False
    if expected == "NICENANO":
        normalized = info.lower().replace("!", "")
        return "nice" in normalized and "nano" in normalized
    return True


def matching_volumes(volumes_root: Path, expected_name: str) -> list[Path]:
    try:
        children: Iterable[Path] = volumes_root.iterdir()
    except OSError:
        return []
    return sorted(
        (path for path in children if path.is_dir() and volume_matches(path, expected_name)),
        key=str,
    )


def wait_for_volume(volumes_root: Path, expected_name: str, poll: float) -> Path:
    while True:
        matches = matching_volumes(volumes_root, expected_name)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(str(path) for path in matches)
            raise FlashError(f"Multiple matching bootloader volumes: {names}")
        time.sleep(poll)


def copy_firmware(firmware: Firmware, volume: Path) -> tuple[Path, bool]:
    """Copy the UF2 and return (destination, whether every byte was confirmed written)."""
    destination = volume / firmware.path.name
    written = 0
    final_chunk = False
    try:
        with firmware.path.open("rb") as source, destination.open("wb", buffering=0) as output:
            while True:
                chunk = source.read(64 * 1024)
                if not chunk:
                    break
                final_chunk = written + len(chunk) == firmware.size
                remaining = memoryview(chunk)
                while remaining:
                    count = output.write(remaining)
                    if not count:
                        raise OSError("write returned zero bytes")
                    written += count
                    remaining = remaining[count:]
            os.fsync(output.fileno())
        os.sync()
    except OSError as error:
        # macOS can report EIO on the last write when the bootloader receives the
        # final UF2 block and reboots before the write call returns
        if written == firmware.size or final_chunk:
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                if not volume.exists():
                    return destination, written == firmware.size
                time.sleep(0.05)
        raise FlashError(
            f"Transfer failed after {written}/{firmware.size} bytes: {error}"
        ) from error
    if written != firmware.size:
        raise FlashError(f"Short transfer: wrote {written}/{firmware.size} bytes")
    return destination, True


def verify_transfer(
    firmware: Firmware,
    volume: Path,
    destination: Path,
    reboot_timeout: float,
    poll: float,
) -> str:
    deadline = time.monotonic() + reboot_timeout
    while time.monotonic() < deadline:
        if not volume.exists():
            return "bootloader accepted the full transfer and rebooted"
        try:
            if destination.is_file() and destination.stat().st_size == firmware.size:
                if sha256_file(destination) == firmware.sha256:
                    return "destination size and SHA-256 verified"
        except OSError:
            if not volume.exists():
                return "bootloader accepted the full transfer and rebooted"
        time.sleep(poll)
    raise FlashError(
        f"Transfer wrote fully, but could not verify it within {reboot_timeout:g}s"
    )


def wait_until_absent(volumes_root: Path, expected_name: str, poll: float) -> None:
    stable_since: float | None = None
    while True:
        if matching_volumes(volumes_root, expected_name):
            stable_since = None
        elif stable_since is None:
            stable_since = time.monotonic()
        elif time.monotonic() - stable_since >= 1.0:
            return
        time.sleep(poll)


def flash_one(
    firmware: Firmware,
    index: int,
    total: int,
    volumes_root: Path,
    volume_name: str,
    reboot_timeout: float,
    poll: float,
) -> bool:
    print()
    print(f"[{index}/{total}] {firmware.side.upper()} HALF")
    print(f"Firmware: {firmware.path}")
    print(f"SHA-256: {firmware.sha256}")
    print(f"Plug in the {firmware.side} half and double-tap reset.")
    print(f"Waiting for {volume_name}...", flush=True)
    volume = wait_for_volume(volumes_root, volume_name, poll)
    print(f"Found {volume}. Flashing now...", flush=True)
    destination, confirmed = copy_firmware(firmware, volume)
    if confirmed:
        verification = verify_transfer(
            firmware, volume, destination, reboot_timeout, poll
        )
        print(f"\aDONE: {firmware.side} half — {verification}.", flush=True)
    else:
        print(
            f"\aUNCONFIRMED: {firmware.side} half — the bootloader rebooted during "
            "the final write, so the last bytes could not be confirmed. "
            "Check that the half works; reflash if it does not.",
            flush=True,
        )
    print(f"You can disconnect the {firmware.side} half.", flush=True)
    print("Waiting for the bootloader volume to disconnect...", flush=True)
    wait_until_absent(volumes_root, volume_name, poll)
    return confirmed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wait for each Keyball61 half and flash its ZMK UF2 automatically."
    )
    parser.add_argument(
        "firmware",
        nargs="*",
        type=Path,
        help="UF2 file, firmware.zip, or directory; half inferred from filename",
    )
    parser.add_argument("--left", type=Path, help="Left UF2 file, zip, or directory")
    parser.add_argument("--right", type=Path, help="Right UF2 file, zip, or directory")
    parser.add_argument(
        "--volume-name", default="NICENANO", help="UF2 bootloader volume name"
    )
    parser.add_argument(
        "--check", action="store_true", help="Validate artifacts without flashing"
    )
    parser.add_argument(
        "--reboot-timeout",
        type=float,
        default=15.0,
        help="seconds allowed for transfer verification (default: 15)",
    )
    parser.add_argument(
        "--volumes-root",
        type=Path,
        default=Path("/Volumes"),
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.firmware and args.left is None and args.right is None:
        print("error: provide firmware files or --left/--right", file=sys.stderr)
        return 2
    if args.reboot_timeout <= 0:
        print("error: --reboot-timeout must be positive", file=sys.stderr)
        return 2

    try:
        with ExitStack() as stack:
            firmware = resolve_firmware(
                args.firmware,
                {"left": args.left, "right": args.right},
                stack,
            )
            print("Keyball61 firmware plan:")
            for image in firmware:
                print(
                    f"  {image.side:>5}: {image.path.name} "
                    f"({image.size} bytes, {image.blocks} UF2 blocks)"
                )
                print(f"         SHA-256 {image.sha256}")
            if args.check:
                print("Artifact validation passed; no device was changed.")
                return 0
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                raise FlashError("Flashing requires an interactive terminal (TTY)")

            poll = 0.25
            all_confirmed = True
            for index, image in enumerate(firmware, 1):
                all_confirmed &= flash_one(
                    image,
                    index,
                    len(firmware),
                    args.volumes_root,
                    args.volume_name,
                    args.reboot_timeout,
                    poll,
                )
            if all_confirmed:
                print("\n\aAll requested firmware transfers completed and were checked.")
            else:
                print("\n\aTransfers finished, but at least one is unconfirmed (see above).")
            print("Reconnect over Bluetooth/USB and test keys and pointer movement.")
            return 0
    except KeyboardInterrupt:
        print("\nCancelled; no further halves will be flashed.", file=sys.stderr)
        return 130
    except FlashError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
