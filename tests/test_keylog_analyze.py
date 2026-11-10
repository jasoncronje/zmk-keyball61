import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "tools" / "keylog" / "analyze.py"
SPEC = importlib.util.spec_from_file_location("keylog_analyze", SCRIPT)
analyze = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = analyze
SPEC.loader.exec_module(analyze)

POS, KEY, LAYER = analyze.POSITION, analyze.KEYCODE, analyze.LAYER
LSHIFT, Y, T, U, N1 = 0xE1, 28, 23, 24, 30


def write_db(path: Path, events: list[tuple[int, int, int, int, int, int]]) -> None:
    """events: (kind, pressed, a, b, c, kb_ms) in arrival order, one session."""
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE sessions(id INTEGER PRIMARY KEY, started REAL NOT NULL, device TEXT);
        CREATE TABLE events(id INTEGER PRIMARY KEY, session INTEGER NOT NULL,
            host_time REAL NOT NULL, seq INTEGER NOT NULL, kind INTEGER NOT NULL,
            flags INTEGER NOT NULL, a INTEGER NOT NULL, b INTEGER NOT NULL,
            c INTEGER NOT NULL, kb_ms INTEGER NOT NULL, app TEXT);
        CREATE TABLE gaps(session INTEGER, host_time REAL NOT NULL, reason TEXT NOT NULL);
        INSERT INTO sessions VALUES (1, 0, 'test');
        INSERT INTO gaps VALUES (1, 0, 'secure input on');
        """
    )
    con.executemany(
        "INSERT INTO events(session, host_time, seq, kind, flags, a, b, c, kb_ms, app)"
        " VALUES (1, 0, 0, ?, ?, ?, ?, ?, ?, 'com.example.editor')",
        events,
    )
    con.commit()
    con.close()


def tap(position: int, code: int, down: int, up: int, mods: int = 0) -> list[tuple]:
    return [
        (POS, 1, position, 255, 0, down),
        (KEY, 1, 7, mods, code, down + 1),
        (POS, 0, position, 255, 0, up),
        (KEY, 0, 7, mods, code, up + 1),
    ]


class KeylogAnalyzeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.keymap = analyze.parse_keymap(analyze.DEFAULT_KEYMAP)

    def test_keymap_layers_and_hold_taps(self) -> None:
        names = [name for name, _ in self.keymap.layers]
        self.assertEqual(names[:3], ["MAIN", "SYMBOL", "FUNCTION"])
        self.assertTrue(all(len(bindings) == 61 for _, bindings in self.keymap.layers))
        self.assertEqual(self.keymap.binding(0, 25).behavior, "hml")
        self.assertEqual(self.keymap.hold_taps["hml"].tapping_term, 260)
        # &trans on SYMBOL falls through to MAIN
        self.assertEqual(self.keymap.binding(1, 36).label, "LEFT_SHIFT")
        self.assertEqual(self.keymap.label(25), "A/LSHIFT")
        self.assertEqual(self.keymap.label(58), "SPACE/SYMBOL")

    def test_report(self) -> None:
        events = []
        events += tap(17, T, 1000, 1080)  # t
        # Home-row A held 120 ms across a right-hand Y: read as Shift+Y
        events += [
            (POS, 1, 25, 255, 0, 1200),
            (POS, 1, 18, 0, 0, 1250),
            (KEY, 1, 7, 0, LSHIFT, 1251),
            (KEY, 1, 7, 0x02, Y, 1252),
            (POS, 0, 18, 0, 0, 1300),
            (KEY, 0, 7, 0x02, Y, 1301),
            (POS, 0, 25, 255, 0, 1320),
            (KEY, 0, 7, 0, LSHIFT, 1321),
        ]
        events += tap(55, analyze.BACKSPACE, 1500, 1560)  # delete the Y
        events += tap(19, U, 1700, 1760)  # u instead
        # Space held for SYMBOL, then ! (Shift+1)
        events += [
            (POS, 1, 58, 0, 0, 2000),
            (LAYER, 1, 1, 1, 0b11, 2160),
            (POS, 1, 13, 255, 0, 2200),
            (KEY, 1, 7, 0x02, N1, 2201),
            (POS, 0, 13, 255, 0, 2260),
            (KEY, 0, 7, 0x02, N1, 2261),
            (POS, 0, 58, 0, 0, 2300),
            (LAYER, 0, 1, 0, 0b01, 2301),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "keylog.sqlite"
            write_db(db, events)
            sessions, gaps = analyze.load(db, None)
        text = analyze.report(sessions, gaps, self.keymap)

        self.assertIn("| Key presses | 7 |", text)
        self.assertIn("secure input on ×1", text)
        # The Shift+Y the roll produced was deleted and replaced with u
        self.assertIn("| Y | 1 | 1 | 100.0% |", text)
        self.assertIn("| Y | u | 1 |", text)
        self.assertIn("A/LSHIFT → Y (held 120 ms, other key released 20 ms before) ×1", text)
        self.assertIn("| A/LSHIFT | MAIN | 25 | 260 | 0 | 1 |", text)
        self.assertIn("| SPACE/SYMBOL | MAIN | 58 | 160 | 0 | 1 |", text)
        self.assertIn("| EXCL | SYMBOL | 13 | 1 |", text)

    def test_merge_streams_dedupes_usb_and_bluetooth(self) -> None:
        # (session, kind, flags, a, b, c, kb_ms, app, host_time)
        usb = [(5, POS, 1, 17, 255, 0, 1000, None, 10.0), (5, KEY, 1, 7, 0, T, 1001, None, 10.0)]
        # Bluetooth delivered the same records plus one USB missed, and started earlier
        ble = [(4, LAYER, 1, 3, 3, 0b1001, 900, None, 9.0)] + [(4, *row[1:]) for row in usb] + [
            (4, POS, 0, 17, 255, 0, 1080, None, 10.1)]
        later = [(6, POS, 1, 18, 255, 0, 50, None, 100.0)]  # after a keyboard reboot
        merged = analyze.merge_streams(ble + usb + later)
        self.assertEqual([(row[0], row[1], row[6]) for row in merged],
                         [(4, LAYER, 900), (4, POS, 1000), (4, KEY, 1001), (4, POS, 1080), (6, POS, 50)])


if __name__ == "__main__":
    unittest.main()
