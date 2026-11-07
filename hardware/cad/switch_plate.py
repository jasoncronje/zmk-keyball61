"""Bottom-screw MX switch plate.

Run `uv run switch_plate.py` to write out/{left,right}_switch_plate.{step,stl,3mf}.
STEP is in the design orientation; STL and 3MF are flipped top-down for printing.
"""

from pathlib import Path

from build123d import (
    Circle,
    Cylinder,
    Kind,
    Mesher,
    Polygon,
    Pos,
    Rectangle,
    Rot,
    Sketch,
    Vector,
    export_step,
    export_stl,
    extrude,
    fillet,
    offset,
)

import layout_left as left
import layout_right as right
from params import (
    body_relief,
    clip_ledge,
    insert_boss_dia,
    insert_depth,
    insert_pilot,
    outline_inset,
    outline_round,
    plate_thick,
    relief_depth,
    switch_cutout,
)

OUT = Path(__file__).parent / "out"


def at(x: float, y: float, angle: float, shape):
    return Pos(x, y) * Rot(0, 0, angle) * shape


def polygon(points) -> Sketch:
    shape = Polygon(*points, align=None)
    if shape.faces()[0].normal_at().Z < 0:  # clockwise points would cut instead of fuse
        shape = Polygon(*reversed(points), align=None)
    return shape


def round_corners(sketch: Sketch, r: float) -> Sketch:
    """Fillet every corner: closing rounds concave corners, opening rounds convex ones."""
    closed = offset(offset(sketch, r, kind=Kind.ARC), -r, kind=Kind.ARC)
    return offset(offset(closed, -r, kind=Kind.ARC), r, kind=Kind.ARC)


def plate_outline(layout) -> Sketch:
    # Neighbouring 1u squares only touch, which leaves them as separate faces, so grow
    # them by `overlap` to fuse them and take it back off in the inset.
    overlap = 0.05
    size = layout.UNIT_SPACING + 2 * overlap
    squares = Sketch() + [at(x, y, a, Rectangle(size, size)) for x, y, a in layout.KEYS]
    outline = offset(squares, -(outline_inset + overlap), kind=Kind.INTERSECTION)
    outline -= [polygon(points) for points in layout.GRID_TRIMS]
    outline += [polygon(points) for points in layout.WEBS]
    for (x, y), r in layout.CORNER_FILLETS:
        corner = min(outline.vertices(), key=lambda v: (v.center() - Vector(x, y)).length)
        assert (corner.center() - Vector(x, y)).length < 0.01, f"no outline corner at {x}, {y}"
        outline = fillet(corner, r)
    outline -= [Pos(x, y) * Circle(r) for x, y, r in layout.OUTLINE_CUTS]
    outline = round_corners(outline, outline_round)
    assert len(outline.faces()) == 1, f"outline split into {len(outline.faces())} faces"
    return outline


def switch_plate(layout):
    keys = layout.KEYS + layout.THUMB_KEYS
    plate = extrude(plate_outline(layout), plate_thick)

    cutouts = Sketch() + [at(x, y, a, Rectangle(switch_cutout, switch_cutout)) for x, y, a in keys]
    plate -= extrude(cutouts, plate_thick)

    reliefs = Sketch() + [at(x, y, a, Rectangle(body_relief, body_relief)) for x, y, a in keys]
    reliefs -= [Pos(x, y) * Circle(insert_boss_dia / 2) for x, y in layout.INSERTS]
    plate -= extrude(reliefs, relief_depth)

    for x, y in layout.INSERTS:
        plate -= Pos(x, y, insert_depth / 2) * Cylinder(insert_pilot / 2, insert_depth)

    assert abs(relief_depth + clip_ledge - plate_thick) < 1e-9
    return plate


def export(part, name: str, flip: bool = True, pose=None, tol=(0.005, 0.05)) -> None:
    """STEP in the design orientation; STL and 3MF as printed (flip turns the part over,
    pose places it any other way). tol is the meshes' (linear, angular) deflection."""
    OUT.mkdir(exist_ok=True)
    export_step(part, OUT / f"{name}.step")
    printable = pose * part if pose else Rot(0, 180, 0) * part if flip else part
    export_stl(printable, OUT / f"{name}.stl", tolerance=tol[0], angular_tolerance=tol[1])
    mesher = Mesher()
    mesher.add_shape(printable, linear_deflection=tol[0], angular_deflection=tol[1])
    mesher.write(OUT / f"{name}.3mf")


PLATES = {"left_switch_plate": left, "right_switch_plate": right}

if __name__ == "__main__":
    for name, layout in PLATES.items():
        plate = switch_plate(layout)
        print(f"{name}: volume {plate.volume:.1f} mm^3, bbox {plate.bounding_box().size}")
        export(plate, name)
