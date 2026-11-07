"""Dust lid that drops over the case: one smooth shell standing on the case rim, its top
rolled over into the sides, with a short skirt down the outside of the case walls. Open over the palm tray, the port, (right
half) the trackball and its holder and (left half) the Touch ID pod.

Run `uv run lid.py` to write out/{left,right}_lid.{step,stl,3mf} and the short
fit-test rings out/{left,right}_lid_test_ring.*. Both print top-down.
"""

from build123d import Box, Circle, Kind, Part, Plane, Pos, Rectangle, Rot, Sketch, Transition, Vector, extrude, offset, sweep

import layout_left as left
import layout_right as right
import touchid
from case import outlines, snaps
from params import (
    case_height,
    case_wall,
    keycap,
    keycap_clearance,
    lid_ball_clearance,
    lid_band,
    lid_clearance,
    lid_height,
    lid_round,
    lid_seat,
    lid_skirt,
    lid_top,
    lid_wall,
    test_ring_skirt,
)
from switch_plate import export, plate_outline

FAR = 50.0  # reach of the cutting boxes past the part


def ball_cut(layout):
    """The plate's trackball cutout (x, y, radius), or None on the left half."""
    if layout.TRACKBALL_HOLE is None:
        return None
    return max(layout.OUTLINE_CUTS, key=lambda c: c[2])


def rounded_prism(sk: Sketch, z0: float, z1: float, r: float):
    """sk extruded from z0 to z1, its top edge rolled over on radius r: a quarter disc
    swept round sk inset by r, on that inset extruded to z1 (fillets, 3D offsets and lofts
    between offsets all fail or leave seams on the case outline). sk's convex corners need
    a radius over r."""
    core = Sketch() + offset(sk, -r, kind=Kind.ARC).faces()
    path = Pos(0, 0, z1 - r) * core.faces()[0].outer_wire()
    at, t = path @ 0, (path % 0).normalized()
    n = Vector(t.Y, -t.X, 0)
    if core.faces()[0].is_inside(Vector(at.X, at.Y, 0) + n * 0.5):
        n = -n
    quarter = Plane(origin=at, x_dir=n, z_dir=-t) * (Circle(r) & Pos(r / 2, r / 2) * Rectangle(r, r))
    roll = sweep(quarter, path=path, transition=Transition.ROUND)
    return Pos(0, 0, z0) * extrude(sk, z1 - r - z0) + Pos(0, 0, z0) * extrude(core, z1 - z0) + roll


def lid(layout):
    _, outer, _ = outlines(layout)
    skirt_in = offset(outer, lid_clearance, kind=Kind.ARC)
    skirt_out = offset(outer, lid_clearance + lid_wall, kind=Kind.ARC)
    # Across the palm tray the lid's front is flush with the case front, standing on the
    # case's front wall: no skirt or overhang to reach the wooden rest
    edge, reach, span = layout.TRAY_EDGE_X, lid_clearance + lid_wall, 4 * FAR
    # the right half's tray runs to +x from its free edge, the left half's to -x
    x0, x1 = (edge - reach, edge + span) if edge > 0 else (edge - span, edge + reach)
    skirt_out -= Pos((x0 + x1) / 2, layout.CASE_FRONT - FAR / 2) * Rectangle(x1 - x0, FAR)
    # round off every convex corner to more than lid_round, so the roll can follow them
    shrunk = Sketch() + offset(skirt_out, -lid_round - 0.5, kind=Kind.ARC).faces()
    shell_out = Sketch() + offset(shrunk, lid_round + 0.5, kind=Kind.ARC).faces()
    shell_in = Sketch() + offset(shell_out, -lid_wall, kind=Kind.ARC).faces()

    # One smooth shell: straight sides from the skirt's foot, rolling over into the top
    skirt_z = case_height - lid_skirt
    part = rounded_prism(shell_out, skirt_z, lid_height, lid_round)
    # the skirt is the shell less the case, minus anything thinner than 1 mm (it tapers to a
    # knife edge where the thumb curve meets the palm tray front)
    ring = Sketch() + offset(Sketch() + offset(shell_out - skirt_in, -0.5, kind=Kind.ARC).faces(), 0.5, kind=Kind.ARC).faces()
    part -= Pos(0, 0, skirt_z) * extrude(shell_out - ring, lid_skirt)
    # snap bumps inside the skirt, into the case's dimples
    part += Pos(0, 0, skirt_z) * extrude(shell_out, lid_skirt) & (Part() + snaps(layout))  # nothing through the outside
    # open over the USB/switch port, the full skirt height
    (px0, _), (px1, py1) = layout.PORT
    part -= Pos((px0 + px1) / 2, py1, case_height / 2) * Box(px1 - px0, FAR, case_height)

    # Inside, the lid stands on the rim out to the case wall's inner face, then flares out
    # at 45 degrees to the shell's inside (a ledge there would be an overhang upside down)
    band_in = Sketch() + offset(outer, -case_wall, kind=Kind.ARC).faces()
    # (in 0.5 mm steps: a loft between the outlines twists into fins at sharp corners)
    steps = round(lid_seat / 0.5)
    seat = Part() + [
        Pos(0, 0, case_height + lid_seat * k / steps)
        * extrude(offset(band_in, lid_seat * k / steps, kind=Kind.ARC) if k else band_in, lid_height)
        for k in range(steps + 1)
    ]
    part -= rounded_prism(shell_in, case_height, lid_height - lid_top, lid_round - lid_wall) & seat
    # and keycap_clearance round every cap, where the case wall is relieved past the seat
    side = keycap + 2 * keycap_clearance
    part -= [Pos(x, y, case_height) * Rot(0, 0, a) * extrude(Rectangle(side, side), lid_band - 1.0)
             for x, y, a in layout.KEYS + layout.THUMB_KEYS]

    # The Touch ID pod stands outside the case wall, up to the rim: no skirt over it
    if layout.POD_CENTER:
        clear = offset(touchid.pod_plan(layout), lid_clearance, kind=Kind.ARC)
        part -= extrude(clear, case_height)

    # Over the trackball: the plate's round cutout, and right of the ball's centre the
    # plate's own cutout lines round the ball holder, from the rim up
    ball = ball_cut(layout)
    if ball is not None:
        x, y, r = ball
        opening = Sketch()
        if layout.LID_HOLDER_BOX is not None:
            (x0, y0), (x1, y1) = layout.LID_HOLDER_BOX
            holder = Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0) - plate_outline(layout)
            # straight out through the front: a strip in front of the holder hit the ball cup
            opening += max(holder.faces(), key=lambda f: f.area)  # drop slivers along the plate edge
        # round the ball, lid_ball_clearance past the plate's cutout and straight out through
        # the front: the ball's front is ~2 mm off the case front, no room for a strip there
        r += lid_ball_clearance
        opening += Pos(x, y) * Circle(r) + Pos(x, y - FAR) * Rectangle(2 * r, 2 * FAR)
        part -= Pos(0, 0, case_height) * extrude(opening, lid_height - case_height)

    assert len(part.solids()) == 1, f"lid split into {len(part.solids())} solids"
    return part


def test_ring(part):
    """The bottom of the skirt plus a band slice, to check the fit on the case before
    printing a whole lid. Flipped like the lid, the band is the first layer."""
    z0, z1 = case_height - test_ring_skirt, case_height + lid_top
    bb = part.bounding_box()
    slab = Pos(bb.center().X, bb.center().Y, (z0 + z1) / 2) * Box(bb.size.X + 10, bb.size.Y + 10, z1 - z0)
    return Pos(0, 0, -z0) * (part & slab)


LIDS = {"left_lid": left, "right_lid": right}

if __name__ == "__main__":
    for name, layout in LIDS.items():
        part = lid(layout)
        print(f"{name}: volume {part.volume:.1f} mm^3, bbox {part.bounding_box().size}")
        export(part, name)
        export(test_ring(part), f"{name}_test_ring")
