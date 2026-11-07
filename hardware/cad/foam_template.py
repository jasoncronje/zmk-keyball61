"""1:1 cutting template for the foam under each keyboard PCB.

    uv run foam_template.py   ->  out/foam_template.pdf (one Letter page per half)

The foam lies on the case floor, under the PCB: the shape is the floor the case leaves
free at that height (inside the walls, round the standoffs and the Touch ID pod), less
`foam_clearance`, with a cut-out for the trackball sensor on the right. It bridges the
floor pockets. Seen from above, as you look into the case. Print at 100% and check the
50 mm bar.
"""

from build123d import Box, Plane, Pos, Rectangle, Sketch, offset, Kind

from case import CASES, case, outlines
from switch_plate import OUT

foam_clearance = 0.5  # off the walls, standoffs and pod, per side
sensor_margin = 6.0  # round the trackball hole and the sensor board's screws
probe_z = 8.0  # between the case floor (7) and the PCB (9.5)

PAGE = (279.4, 215.9)  # Letter, landscape, mm
PT = 72 / 25.4


def free_floor(name: str, layout) -> Sketch:
    body = case(layout)
    inner = outlines(layout)[0]
    slab = body & Pos(0, 0, probe_z) * Box(1000, 1000, 0.2)
    faces = [f for f in slab.faces() if abs(f.center().Z - (probe_z - 0.1)) < 1e-3]
    solid = Sketch() + [Plane.XY * f.moved(Pos(0, 0, -f.center().Z)) for f in faces]
    foam = inner - offset(solid, foam_clearance, kind=Kind.ARC)
    if layout.TRACKBALL_HOLE:
        pts = [layout.TRACKBALL_HOLE] + list(layout.SENSOR_SCREWS)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        r = 6.0 + sensor_margin  # trackball hole radius
        x0, x1, y0, y1 = min(xs) - r, max(xs) + r, min(ys) - r, max(ys) + r
        foam -= Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0)
    # drop the specks left inside the standoffs' screw holes
    return Sketch() + [f for f in foam.faces() if f.area > 100]


def wire_points(wire, step=0.3):
    n = max(64, int(wire.length / step))
    return [(p.X, p.Y) for p in (wire @ (i / n) for i in range(n))]


def page(foam: Sketch, title: str) -> str:
    bb = foam.bounding_box()
    # centre the shape on the page, a little above middle to leave room for the notes
    dx = PAGE[0] / 2 - (bb.min.X + bb.max.X) / 2
    dy = PAGE[1] / 2 + 8 - (bb.min.Y + bb.max.Y) / 2
    ops = ["0 0 0 RG 0.6 w"]
    for face in foam.faces():
        for wire in [face.outer_wire(), *face.inner_wires()]:
            pts = wire_points(wire)
            ops.append(" ".join(
                f"{(x + dx) * PT:.2f} {(y + dy) * PT:.2f} {'m' if i == 0 else 'l'}" for i, (x, y) in enumerate(pts)
            ) + " h S")
    # 50 mm check bar
    x0, y0 = 20, 16
    ops.append(f"1.2 w {x0 * PT:.2f} {y0 * PT:.2f} m {(x0 + 50) * PT:.2f} {y0 * PT:.2f} l S")
    for x in (x0, x0 + 50):
        ops.append(f"{x * PT:.2f} {(y0 - 2) * PT:.2f} m {x * PT:.2f} {(y0 + 2) * PT:.2f} l S")
    w, h = bb.max.X - bb.min.X, bb.max.Y - bb.min.Y
    lines = [
        (title, 14),
        (f"Print at 100% (Actual size). The bar must measure 50 mm. Shape {w:.1f} x {h:.1f} mm.", 9),
        ("Seen from above: lay it on the foam's top face. With adhesive foam, the backing paper is the mirror image.", 9),
    ]
    y = PAGE[1] - 14
    for text, size in lines:
        ops.append(f"BT /F1 {size} Tf {14 * PT:.2f} {y * PT:.2f} Td ({text}) Tj ET")
        y -= size * 0.55
    ops.append(f"BT /F1 9 Tf {(x0 + 54) * PT:.2f} {(y0 - 1) * PT:.2f} Td (50 mm) Tj ET")
    return "\n".join(ops)


def write_pdf(path, streams):
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for s in streams:
        objs.append(f"<< /Length {len(s)} >>\nstream\n{s}\nendstream")
        objs.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE[0] * PT:.2f} {PAGE[1] * PT:.2f}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {len(objs)} 0 R >>"
        )
        kids.append(f"{len(objs)} 0 R")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offsets = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    path.write_text(out, encoding="latin-1")


def main() -> None:
    streams = []
    for name, layout in CASES.items():
        half = name.split("_")[0].upper()
        streams.append(page(free_floor(name, layout), f"Keyball61 {half} - foam under the PCB"))
    path = OUT / "foam_template.pdf"
    write_pdf(path, streams)
    print("->", path)


if __name__ == "__main__":
    main()
