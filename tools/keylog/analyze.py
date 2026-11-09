#!/usr/bin/env python3
"""Turn the key log (tools/keylog/keylogd) into tuning notes for the keymap.

Reads ~/Library/Application Support/keyball-keylog/keylog.sqlite and
config/keyball61.keymap, and prints a Markdown report: key and layer use,
what gets deleted with Backspace, how the hold-taps decide, auto-mouse clicks
right after typing, and same-finger pairs.

    python3 tools/keylog/analyze.py [--db PATH] [--keymap PATH] [--days N]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median

DEFAULT_DB = Path.home() / "Library/Application Support/keyball-keylog/keylog.sqlite"
DEFAULT_KEYMAP = Path(__file__).resolve().parents[2] / "config/keyball61.keymap"

POSITION, KEYCODE, LAYER, DROPPED = 1, 2, 3, 4
PAGE_KEY = 0x07

# Physical layout (config/keyball61.keymap position map): position -> (row, column)
ROWS = [
    list(range(0, 6)) + [None] * 2 + list(range(6, 12)),
    list(range(12, 18)) + [None] * 2 + list(range(18, 24)),
    list(range(24, 30)) + [None] * 2 + list(range(30, 36)),
    list(range(36, 43)) + list(range(43, 50)),
    list(range(50, 57)) + [57, 58] + [None] * 3 + [59, 60],
]
THUMBS = {54, 55, 56, 57, 58}
MOUSE_LAYER = 3
AUTO_MOUSE_EXCLUDED = {20, 31, 32, 33, 34, 46}  # zip_temp_layer excluded-positions

# HID keyboard usages for the names the keymap uses
KEY_CODES: dict[str, int] = {chr(ord("A") + i): 4 + i for i in range(26)}
KEY_CODES.update({f"N{(i + 1) % 10}": 30 + i for i in range(10)})
KEY_CODES.update({f"F{i}": 57 + i for i in range(1, 13)})
KEY_CODES.update({f"F{i}": 91 + i for i in range(13, 25)})
KEY_CODES.update(
    ENTER=40, RET=40, ESC=41, ESCAPE=41, BSPC=42, BACKSPACE=42, TAB=43, SPACE=44,
    MINUS=45, EQUAL=46, LBKT=47, RBKT=48, BSLH=49, BACKSLASH=49, SEMI=51,
    SEMICOLON=51, SQT=52, APOS=52, GRAVE=53, COMMA=54, DOT=55, FSLH=56, SLASH=56,
    CAPSLOCK=57, CAPS=57, PAGE_UP=75, PG_UP=75, DELETE=76, DEL=76, PAGE_DOWN=78,
    PG_DN=78, RIGHT=79, RIGHT_ARROW=79, LEFT=80, LEFT_ARROW=80, DOWN=81,
    DOWN_ARROW=81, UP=82, UP_ARROW=82,
    LCTRL=0xE0, LEFT_CONTROL=0xE0, LSHIFT=0xE1, LEFT_SHIFT=0xE1, LSHFT=0xE1,
    LALT=0xE2, LEFT_ALT=0xE2, LGUI=0xE3, LCMD=0xE3, LEFT_COMMAND=0xE3,
    RCTRL=0xE4, RIGHT_CONTROL=0xE4, RSHIFT=0xE5, RIGHT_SHIFT=0xE5, RALT=0xE6,
    RIGHT_ALT=0xE6, RGUI=0xE7, RCMD=0xE7, RIGHT_COMMAND=0xE7,
)
MOD_NAMES = ["Ctrl", "Shift", "Opt", "Cmd", "Ctrl", "Shift", "Opt", "Cmd"]
BACKSPACE = 42

PLAIN = {
    **{4 + i: chr(ord("a") + i) for i in range(26)},
    **{30 + i: str((i + 1) % 10) for i in range(10)},
    40: "⏎", 41: "Esc", 42: "⌫", 43: "Tab", 44: "␣", 45: "-", 46: "=", 47: "[",
    48: "]", 49: "\\", 51: ";", 52: "'", 53: "`", 54: ",", 55: ".", 56: "/",
    57: "Caps", 75: "PgUp", 76: "Del", 78: "PgDn", 79: "→", 80: "←", 81: "↓", 82: "↑",
}
SHIFTED = {
    **{4 + i: chr(ord("A") + i) for i in range(26)},
    **dict(zip(range(30, 40), "!@#$%^&*()")),
    45: "_", 46: "+", 47: "{", 48: "}", 49: "|", 51: ":", 52: '"', 53: "~",
    54: "<", 55: ">", 56: "?",
}


def key_name(page: int, code: int, mods: int = 0) -> str:
    if page != PAGE_KEY:
        return f"media:{code:#x}"
    if 0xE0 <= code <= 0xE7:
        return MOD_NAMES[code - 0xE0]
    shift = mods & 0x22
    other = [MOD_NAMES[i] for i in range(8) if mods & (1 << i) and i not in (1, 5)]
    base = SHIFTED.get(code) if shift and code in SHIFTED else PLAIN.get(code)
    if base is None:
        base = f"F{code - 57}" if 58 <= code <= 69 else f"F{code - 91}" if 104 <= code <= 115 else f"#{code}"
        if shift:
            other.insert(0, "Shift")
    return "+".join(dict.fromkeys(other)) + ("+" if other else "") + base


# ─── Keymap ────────────────────────────────────────────────────────────────


@dataclass
class Binding:
    behavior: str
    params: list[str]

    @property
    def label(self) -> str:
        if self.behavior == "kp":
            return self.params[0]
        if self.behavior in ("trans", "none"):
            return "·" if self.behavior == "trans" else "∅"
        return " ".join([self.behavior, *self.params])


@dataclass
class HoldTap:
    name: str
    tapping_term: int
    hold: str  # "kp" or "mo"
    tap: str


@dataclass
class Keymap:
    layers: list[tuple[str, list[Binding]]]
    hold_taps: dict[str, HoldTap]

    def binding(self, layer: int, position: int) -> Binding:
        """The binding that runs on this layer, falling through &trans."""
        for index in range(min(layer, len(self.layers) - 1), -1, -1):
            bindings = self.layers[index][1]
            if position < len(bindings) and bindings[position].behavior != "trans":
                return bindings[position]
        return Binding("none", [])

    def label(self, position: int, layer: int = 0) -> str:
        binding = self.binding(layer, position)
        ht = self.hold_taps.get(binding.behavior)
        if ht and len(binding.params) == 2:
            hold, tap = binding.params
            if ht.hold == "mo" and hold.isdigit() and int(hold) < len(self.layers):
                hold = self.layers[int(hold)][0]
            if ht.tap == "none":
                return f"hold {hold}"
            if ht.tap != "kp":
                tap = ht.tap  # the tap runs its own behavior; the parameter is unused
            return f"{tap}/{hold}"
        return binding.label


def strip_comments(text: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)


def parse_keymap(path: Path) -> Keymap:
    text = strip_comments(path.read_text())
    defines = dict(re.findall(r"^#define\s+(\w+)\s+(\S+)\s*$", text, flags=re.M))

    hold_taps: dict[str, HoldTap] = {}
    for label, body in re.findall(r"(\w+)\s*:\s*[\w-]+\s*\{([^{}]*?zmk,behavior-hold-tap[^{}]*?)\}", text, flags=re.S):
        term = re.search(r"tapping-term-ms\s*=\s*<(\d+)>", body)
        behaviors = re.findall(r"<&(\w+)>", re.search(r"bindings\s*=([^;]*);", body).group(1))
        hold_taps[label] = HoldTap(label, int(term.group(1)) if term else 200, behaviors[0], behaviors[1])
    # Built-in hold-taps and their overrides at the top of the keymap
    for label, hold, tap, default in (("lt", "mo", "kp", 200), ("mt", "kp", "kp", 200)):
        override = re.search(rf"&{label}\s*\{{[^}}]*tapping-term-ms\s*=\s*<(\d+)>", text, flags=re.S)
        hold_taps[label] = HoldTap(label, int(override.group(1)) if override else default, hold, tap)

    keymap_body = text[text.index("zmk,keymap"):]
    layers = []
    for name, block in re.findall(r"(\w+)\s*\{[^{}]*?bindings\s*=\s*<([^>]*)>\s*;", keymap_body, flags=re.S):
        label = re.search(rf"{name}\s*\{{[^{{}}]*?label\s*=\s*\"([^\"]+)\"", keymap_body, flags=re.S)
        bindings = []
        for chunk in block.split("&")[1:]:
            words = [defines.get(word, word) for word in chunk.split()]
            bindings.append(Binding(words[0], words[1:]))
        layers.append((label.group(1) if label else name, bindings))
    return Keymap(layers, hold_taps)


def finger(position: int) -> tuple[str, str] | None:
    """(hand, finger) by column; thumbs return None."""
    if position in THUMBS:
        return None
    for row in ROWS:
        if position in row:
            column = row.index(position)
            break
    else:
        return None
    if column < 7:
        names = ["pinky", "pinky", "ring", "middle", "index", "index", "index"]
        return "L", names[column]
    names = ["index", "index", "index", "middle", "ring", "pinky", "pinky"]
    return "R", names[column - 7]


# ─── Events ────────────────────────────────────────────────────────────────


@dataclass
class Press:
    position: int
    down: int
    layer: int  # highest active layer when pressed
    app: str | None
    up: int | None = None
    keycodes: list[tuple[int, int, int, int]] = field(default_factory=list)  # (ms, page, code, mods)
    layers_on: list[int] = field(default_factory=list)


@dataclass
class KeyPress:
    ms: int
    page: int
    code: int
    mods: int
    layer: int
    app: str | None


@dataclass
class Session:
    presses: list[Press] = field(default_factory=list)
    keys: list[KeyPress] = field(default_factory=list)
    layer_on: list[tuple[int, int]] = field(default_factory=list)  # (ms, layer)


def load(db: Path, since: float | None) -> tuple[list[Session], Counter]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    where = "WHERE host_time >= ?" if since else ""
    rows = con.execute(
        f"SELECT session, kind, flags, a, b, c, kb_ms, app FROM events {where} ORDER BY session, id",
        (since,) if since else (),
    )
    sessions: dict[int, Session] = defaultdict(Session)
    open_presses: dict[tuple[int, int], Press] = {}
    highest: dict[int, int] = defaultdict(int)
    for session_id, kind, flags, a, b, c, ms, app in rows:
        session = sessions[session_id]
        pressed = bool(flags & 1)
        if kind == POSITION:
            key = (session_id, a)
            if pressed:
                press = Press(a, ms, highest[session_id], app)
                session.presses.append(press)
                open_presses[key] = press
            elif key in open_presses:
                open_presses.pop(key).up = ms
        elif kind == KEYCODE and pressed:
            session.keys.append(KeyPress(ms, a, c, b, highest[session_id], app))
            for (owner, _), press in open_presses.items():
                if owner == session_id:
                    press.keycodes.append((ms, a, c, b))
        elif kind == KEYCODE:
            # A tap decided on release sends its key right after the release
            for press in reversed(session.presses[-4:]):
                if press.up is not None and 0 <= ms - press.up <= 50 and not press.keycodes:
                    press.keycodes.append((ms, a, c, b))
                    break
        elif kind == LAYER:
            highest[session_id] = b
            if pressed:
                session.layer_on.append((ms, a))
                for (owner, _), press in open_presses.items():
                    if owner == session_id:
                        press.layers_on.append(a)
    gaps = Counter(reason.split(":")[0] for (reason,) in con.execute(
        f"SELECT reason FROM gaps {where}", (since,) if since else ()))
    return list(sessions.values()), gaps


# ─── Report ────────────────────────────────────────────────────────────────


def table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return "_No data yet._\n"
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def pct(values: list[int], q: float) -> int:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def report(sessions: list[Session], gaps: Counter, keymap: Keymap) -> str:
    out: list[str] = []
    presses = [p for s in sessions for p in s.presses]
    keys = [k for s in sessions for k in s.keys]
    out.append("# Keyball61 key log report\n")
    apps = Counter(p.app or "?" for p in presses)
    out.append(table(["Measure", "Value"], [
        ["Key presses", len(presses)],
        ["Keycodes sent", len(keys)],
        ["Sessions", len(sessions)],
        ["Top apps", ", ".join(f"{a} ({n})" for a, n in apps.most_common(3)) or "-"],
        ["Gaps", ", ".join(f"{r} ×{n}" for r, n in gaps.most_common()) or "none"],
    ]))

    # Layers
    out.append("\n## Layers\n")
    layer_names = [name for name, _ in keymap.layers]
    layer_counts = Counter(p.layer for p in presses)
    out.append(table(["Layer", "Presses", "Share"], [
        [layer_names[l] if l < len(layer_names) else l, n, f"{n / len(presses):.1%}"]
        for l, n in layer_counts.most_common()
    ]))

    # Keys
    out.append("\n## Most and least used keys\n")
    by_key = Counter((p.layer, p.position) for p in presses)
    out.append(table(["Key", "Layer", "Position", "Presses"], [
        [keymap.label(pos, layer), layer_names[layer] if layer < len(layer_names) else layer, pos, n]
        for (layer, pos), n in by_key.most_common(15)
    ]))
    used = {pos for _, pos in by_key}
    unused = [f"{keymap.label(pos)} ({pos})" for pos in range(61)
              if pos not in used and keymap.binding(0, pos).behavior not in ("none", "trans")]
    out.append(f"\nNever pressed on any layer: {', '.join(unused) if unused else 'none'}\n")

    # Backspace
    out.append("\n## Backspace: what gets deleted\n")
    typed, deleted, fixes, runs = Counter(), Counter(), Counter(), Counter()
    for session in sessions:
        ks = [k for k in session.keys if k.page == PAGE_KEY and not 0xE0 <= k.code <= 0xE7]
        i = 0
        while i < len(ks):
            k = ks[i]
            if k.code != BACKSPACE:
                typed[key_name(k.page, k.code, k.mods)] += 1
                i += 1
                continue
            run_start = i
            while i < len(ks) and ks[i].code == BACKSPACE and (i == run_start or ks[i].ms - ks[i - 1].ms < 1500):
                i += 1
            run = i - run_start
            runs[min(run, 6)] += 1
            if run_start > 0 and ks[run_start - 1].code != BACKSPACE and ks[run_start].ms - ks[run_start - 1].ms < 3000:
                before = ks[run_start - 1]
                gone = key_name(before.page, before.code, before.mods)
                deleted[gone] += 1
                if run == 1 and i < len(ks):
                    fixes[(gone, key_name(ks[i].page, ks[i].code, ks[i].mods))] += 1
    total_bs = sum(runs.values())
    lengths = ", ".join(f"{n}{'+' if n == 6 else ''} long: {c}" for n, c in sorted(runs.items()))
    out.append(f"Backspace runs: {total_bs} ({lengths or 'none'})\n\n")
    out.append(table(["Key typed then deleted", "Times", "Of typed", "Rate"], [
        [k, n, typed[k], f"{n / typed[k]:.1%}" if typed[k] else "-"] for k, n in deleted.most_common(15)
    ]))
    out.append("\nSingle-character fixes (typed → replaced with):\n\n")
    out.append(table(["Typed", "Replaced with", "Times"], [
        [a, b, n] for (a, b), n in fixes.most_common(15) if a != b
    ]))

    # Hold-taps
    out.append("\n## Hold-taps\n")
    out.append("Hold time is press to release. Taps longer than the tapping term only resolved as taps "
               "because no other key interrupted (or the positional rule kept them taps).\n\n")
    rows = []
    misfires: list[str] = []
    for (layer, pos) in sorted({(p.layer, p.position) for p in presses}):
        binding = keymap.binding(layer, pos)
        ht = keymap.hold_taps.get(binding.behavior)
        if not ht or len(binding.params) < 2:
            continue
        hold_param, tap_param = binding.params[0], binding.params[1]
        hold_code = KEY_CODES.get(hold_param) if ht.hold == "kp" else None
        hold_layer = int(hold_param) if ht.hold == "mo" and hold_param.isdigit() else None
        taps, holds = [], []
        for session in sessions:
            for i, p in enumerate(session.presses):
                if p.position != pos or p.layer != layer or p.up is None:
                    continue
                held = p.up - p.down
                is_hold = (hold_code is not None and any(c == hold_code for _, _, c, _ in p.keycodes)) or (
                    hold_layer is not None and hold_layer in p.layers_on)
                (holds if is_hold else taps).append(held)
                if is_hold and held < ht.tapping_term:
                    nxt = session.presses[i + 1] if i + 1 < len(session.presses) else None
                    if nxt and nxt.up is not None and nxt.up <= p.up and p.up - nxt.up < 60:
                        misfires.append(f"{keymap.label(pos, layer)} → {keymap.label(nxt.position, layer)} "
                                        f"(held {held} ms, other key released {p.up - nxt.up} ms before)")
        if not taps and not holds:
            continue
        rows.append([
            keymap.label(pos, layer), layer_names[layer] if layer < len(layer_names) else layer, pos,
            ht.tapping_term, len(taps), len(holds),
            f"{median(taps):.0f} / {pct(taps, 0.95)}" if taps else "-",
            f"{median(holds):.0f} / {pct(holds, 0.05)}" if holds else "-",
            sum(1 for t in taps if t > ht.tapping_term),
        ])
    out.append(table(["Key", "Layer", "Pos", "Term ms", "Taps", "Holds", "Tap ms median / p95",
                      "Hold ms median / p5", "Taps over term"], rows))
    out.append("\nShort holds ended right after the other key (likely rolls read as a modifier):\n\n")
    out.append("\n".join(f"- {m} ×{n}" for m, n in Counter(misfires).most_common(15)) or "_None found._")
    out.append("\n")

    # Auto-mouse
    out.append("\n## Auto-mouse layer\n")
    accidental = Counter()
    mouse_presses = 0
    for session in sessions:
        last_typing = None
        for p in session.presses:
            if p.layer == MOUSE_LAYER:
                mouse_presses += 1
                binding = keymap.layers[MOUSE_LAYER][1][p.position] if MOUSE_LAYER < len(keymap.layers) else None
                if binding and binding.behavior not in ("trans", "none") and last_typing is not None \
                        and p.down - last_typing < 400:
                    accidental[binding.label] += 1
            elif p.layer == 0 and p.position not in THUMBS:
                last_typing = p.down
    out.append(f"Presses on the MOUSE layer: {mouse_presses}. Mouse-layer actions under 400 ms after "
               f"typing on MAIN (likely the ball moved while typing):\n\n")
    out.append(table(["Action", "Times"], [[k, n] for k, n in accidental.most_common()]))

    # Same-finger pairs
    out.append("\n## Same-finger pairs (MAIN layer, within 1 s)\n")
    sfb, pairs = Counter(), 0
    for session in sessions:
        main = [p for p in session.presses if p.layer == 0]
        for a, b in zip(main, main[1:]):
            if b.down - a.down > 1000:
                continue
            pairs += 1
            fa, fb = finger(a.position), finger(b.position)
            if fa and fa == fb and a.position != b.position:
                sfb[(keymap.label(a.position), keymap.label(b.position), "/".join(fa))] += 1
    out.append(f"{sum(sfb.values())} of {pairs} pairs ({sum(sfb.values()) / pairs:.1%})\n\n" if pairs else "")
    out.append(table(["From", "To", "Finger", "Times"], [[a, b, f, n] for (a, b, f), n in sfb.most_common(15)]))
    return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--keymap", type=Path, default=DEFAULT_KEYMAP)
    parser.add_argument("--days", type=float, help="only the last N days")
    args = parser.parse_args()
    if not args.db.exists():
        print(f"No key log at {args.db}; run tools/keylog/keylogd first", file=sys.stderr)
        return 1
    since = time.time() - args.days * 86400 if args.days else None
    sessions, gaps = load(args.db, since)
    print(report(sessions, gaps, parse_keymap(args.keymap)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
