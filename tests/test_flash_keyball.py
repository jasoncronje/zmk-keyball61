import importlib.util
import struct
import sys
import tempfile
import unittest
import zipfile
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "flash-keyball.py"
SPEC = importlib.util.spec_from_file_location("flash_keyball", SCRIPT)
flash_keyball = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = flash_keyball
SPEC.loader.exec_module(flash_keyball)


def write_uf2(path: Path, blocks: int = 2) -> None:
    with path.open("wb") as output:
        for _ in range(blocks):
            block = bytearray(flash_keyball.UF2_BLOCK_SIZE)
            struct.pack_into(
                "<II",
                block,
                0,
                flash_keyball.UF2_MAGIC_START0,
                flash_keyball.UF2_MAGIC_START1,
            )
            struct.pack_into(
                "<I",
                block,
                flash_keyball.UF2_BLOCK_SIZE - 4,
                flash_keyball.UF2_MAGIC_END,
            )
            output.write(block)


class FlashKeyballTests(unittest.TestCase):
    def test_validates_uf2_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keyball61_left.uf2"
            write_uf2(path, 3)
            size, blocks, digest = flash_keyball.validate_uf2(path)
            self.assertEqual(size, 3 * flash_keyball.UF2_BLOCK_SIZE)
            self.assertEqual(blocks, 3)
            self.assertEqual(len(digest), 64)

    def test_rejects_invalid_magic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keyball61_right.uf2"
            path.write_bytes(bytes(flash_keyball.UF2_BLOCK_SIZE))
            with self.assertRaises(flash_keyball.FlashError):
                flash_keyball.validate_uf2(path)

    def test_infers_only_unambiguous_half(self):
        self.assertEqual(flash_keyball.infer_side("keyball61_left-zmk.uf2"), "left")
        self.assertEqual(flash_keyball.infer_side("keyball61-right.uf2"), "right")
        self.assertIsNone(flash_keyball.infer_side("firmware.uf2"))
        self.assertIsNone(flash_keyball.infer_side("left-right.uf2"))

    def test_resolves_both_halves_from_zmk_zip_and_ignores_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left = root / "keyball61_left-nice_oled-zmk.uf2"
            right = root / "keyball61_right-nice_oled-zmk.uf2"
            reset = root / "settings_reset-nice_nano_v2-zmk.uf2"
            for path in (left, right, reset):
                write_uf2(path)
            archive = root / "firmware.zip"
            with zipfile.ZipFile(archive, "w") as output:
                for path in (left, right, reset):
                    output.write(path, path.name)

            with ExitStack() as stack:
                resolved = flash_keyball.resolve_firmware(
                    [archive], {"left": None, "right": None}, stack
                )
                self.assertEqual([item.side for item in resolved], ["left", "right"])

    def test_matches_nicenano_volume_and_verifies_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "keyball61_right-zmk.uf2"
            write_uf2(source)
            size, blocks, digest = flash_keyball.validate_uf2(source)
            firmware = flash_keyball.Firmware("right", source, size, digest, blocks)
            volume = root / "NICENANO"
            volume.mkdir()
            (volume / "INFO_UF2.TXT").write_text(
                "Model: nice!nano\nBoard-ID: nRF52840-niceNano-v2\n"
            )

            self.assertTrue(flash_keyball.volume_matches(volume, "NICENANO"))
            destination, confirmed = flash_keyball.copy_firmware(firmware, volume)
            self.assertTrue(confirmed)
            result = flash_keyball.verify_transfer(
                firmware, volume, destination, reboot_timeout=0.1, poll=0.01
            )
            self.assertEqual(result, "destination size and SHA-256 verified")

    def test_accepts_flush_error_only_after_full_write_and_bootloader_reboot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "keyball61_left-zmk.uf2"
            write_uf2(source)
            size, blocks, digest = flash_keyball.validate_uf2(source)
            firmware = flash_keyball.Firmware("left", source, size, digest, blocks)
            volume = root / "NICENANO"
            volume.mkdir()

            def reboot_on_flush(_file_descriptor):
                volume.rename(root / "disconnected")
                raise OSError("device disappeared")

            with mock.patch.object(
                flash_keyball.os, "fsync", side_effect=reboot_on_flush
            ):
                destination, confirmed = flash_keyball.copy_firmware(firmware, volume)

            self.assertEqual(destination.name, source.name)
            self.assertTrue(confirmed)
            self.assertFalse(volume.exists())

    def test_reports_unconfirmed_when_bootloader_reboots_during_final_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "keyball61_left-zmk.uf2"
            write_uf2(source, 130)
            size, blocks, digest = flash_keyball.validate_uf2(source)
            firmware = flash_keyball.Firmware("left", source, size, digest, blocks)
            volume = root / "NICENANO"
            volume.mkdir()
            real_open = Path.open

            class RebootOnFinalWrite:
                def __init__(self, inner):
                    self.inner = inner
                    self.written = 0

                def write(self, data):
                    if self.written + len(data) == size:
                        volume.rename(root / "disconnected")
                        raise OSError(5, "Input/output error")
                    self.written += len(data)
                    return len(data)

                def fileno(self):
                    return self.inner.fileno()

                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    self.inner.close()

            def fake_open(path, mode="r", *args, **kwargs):
                handle = real_open(path, mode, *args, **kwargs)
                return RebootOnFinalWrite(handle) if "w" in mode else handle

            with mock.patch.object(flash_keyball.Path, "open", fake_open):
                destination, confirmed = flash_keyball.copy_firmware(firmware, volume)

            self.assertEqual(destination.name, source.name)
            self.assertFalse(confirmed)

    def test_rejects_error_before_final_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "keyball61_left-zmk.uf2"
            write_uf2(source, 260)
            size, blocks, digest = flash_keyball.validate_uf2(source)
            firmware = flash_keyball.Firmware("left", source, size, digest, blocks)
            volume = root / "NICENANO"
            volume.mkdir()
            real_open = Path.open

            class FailSecondWrite:
                def __init__(self, inner):
                    self.inner = inner
                    self.calls = 0

                def write(self, data):
                    self.calls += 1
                    if self.calls == 2:
                        volume.rename(root / "disconnected")
                        raise OSError(5, "Input/output error")
                    return len(data)

                def fileno(self):
                    return self.inner.fileno()

                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    self.inner.close()

            def fake_open(path, mode="r", *args, **kwargs):
                handle = real_open(path, mode, *args, **kwargs)
                return FailSecondWrite(handle) if "w" in mode else handle

            with mock.patch.object(flash_keyball.Path, "open", fake_open):
                with self.assertRaises(flash_keyball.FlashError):
                    flash_keyball.copy_firmware(firmware, volume)

    def test_rejects_settings_reset_when_passed_directly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings_reset.uf2"
            write_uf2(path)
            with self.assertRaises(flash_keyball.FlashError):
                flash_keyball.validate_uf2(path)

    def test_rejects_explicit_side_that_conflicts_with_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keyball61_left-zmk.uf2"
            write_uf2(path)
            with ExitStack() as stack:
                with self.assertRaises(flash_keyball.FlashError):
                    flash_keyball.resolve_firmware(
                        [], {"left": None, "right": path}, stack
                    )


if __name__ == "__main__":
    unittest.main()
