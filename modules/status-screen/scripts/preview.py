#!/usr/bin/env python3
"""Renders the status screen layouts to PNGs, built from the firmware's own C.

Compiles src/draw.c, glyphs.c and the layouts with the host compiler against a
stub <zephyr/sys/util.h>, runs scripts/preview.c's sample states and writes one
PNG per display and half, the states side by side:

    python3 modules/status-screen/scripts/preview.py OUT_DIR
"""

import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent
SRC = MODULE / 'src'
TOUCHID_INCLUDE = MODULE.parent / 'touchid-power' / 'include'

UTIL_STUB = """#pragma once
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define CLAMP(v, lo, hi) MIN(MAX(v, lo), hi)
#define DIV_ROUND_UP(n, d) (((n) + (d) - 1) / (d))
"""

DISPLAYS = {
    # name: (defines, layout source, lit colour, dark colour)
    'nice_view': (['-DCONFIG_KEYBALL61_STATUS_SCREEN_NICE_VIEW=1'], 'layout_nice_view.c',
                  (40, 42, 38), (196, 199, 186)),
    'oled': ([], 'layout_oled.c', (235, 240, 255), (8, 8, 12)),
}

PIXEL = 4
GAP = 24


def build_and_run(work, defines, layout):
    stub = work / 'include' / 'zephyr' / 'sys'
    stub.mkdir(parents=True, exist_ok=True)
    (stub / 'util.h').write_text(UTIL_STUB)
    binary = work / f'preview-{layout}'
    sources = [SRC / 'draw.c', SRC / 'glyphs.c', SRC / 'layout_common.c', SRC / layout,
               MODULE / 'scripts' / 'preview.c']
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                    *defines, f'-I{work / "include"}', f'-I{SRC}', f'-I{TOUCHID_INCLUDE}',
                    *map(str, sources), '-o', str(binary)], check=True)
    out = subprocess.run([str(binary)], check=True, capture_output=True, text=True).stdout

    frames = {}
    for block in out.split('= ')[1:]:
        name, *rows = block.strip().split('\n')
        frames[name] = rows
    return frames


def write_png(path, frames, lit, dark):
    width = sum(len(rows[0]) * PIXEL for rows in frames) + GAP * (len(frames) + 1)
    height = max(len(rows) for rows in frames) * PIXEL + GAP * 2
    page = (255, 255, 255)

    pixels = [[page] * width for _ in range(height)]
    x0 = GAP
    for rows in frames:
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                colour = lit if c == '#' else dark
                for dy in range(PIXEL):
                    line = pixels[GAP + y * PIXEL + dy]
                    for dx in range(PIXEL):
                        line[x0 + x * PIXEL + dx] = colour
        x0 += len(rows[0]) * PIXEL + GAP

    raw = b''.join(b'\0' + bytes(v for px in line for v in px) for line in pixels)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack(
            '>I', zlib.crc32(tag + data) & 0xffffffff)

    path.write_bytes(b'\x89PNG\r\n\x1a\n' +
                     chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
                     chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        for display, (defines, layout, lit, dark) in DISPLAYS.items():
            frames = build_and_run(Path(tmp), defines, layout)
            for half in ('right', 'left'):
                picked = [rows for name, rows in frames.items() if name.startswith(half)]
                path = out_dir / f'{display}-{half}.png'
                write_png(path, picked, lit, dark)
                print(path)


if __name__ == '__main__':
    main()
