"""Bottom case with the palm-rest tray, screwed to the switch plate from below.

Run `uv run case.py` to write out/{left,right}_case.{step,stl,3mf}. The case prints
the way it sits, bottom on the bed, so every export is in the design orientation.

Stack: screws come up through counterbores in the floor and the standoffs, through
the PCB (on the standoffs at pcb_z) and into the plate's heat-set inserts.
"""

import math

from build123d import (
    Axis,
    Box,
    Circle,
    Cylinder,
    Kind,
    Part,
    Plane,
    Polygon,
    RectangleRounded,
    Pos,
    Rectangle,
    Rot,
    Sketch,
    Sphere,
    Vector,
    extrude,
    fillet,
    offset,
)

import layout_left as left
import touchid
import layout_right as right
from params import (
    case_bottom_round,
    case_cbore,
    case_cbore_depth,
    case_floor,
    case_height,
    case_shaft_hole,
    case_wall,
    foot_depth,
    foot_dia,
    key_relief_z,
    keycap,
    keycap_clearance,
    lid_skirt,
    min_wall,
    pcb_z,
    pocket_floor,
    ball_cup_r,
    ball_fill_gap,
    ball_fill_round,
    ball_front_wall,
    holder_front_round,
    board_pocket,
    port_recess_floor,
    port_round,
    port_top,
    snap_depth,
    snap_dimple_clearance,
    snap_len,
    snap_r,
    sensor_screw_hole,
    standoff_dia,
    trackball_hole,
    tray_corner_round,
    tray_floor,
    tray_wall_cove,
    tray_wall_height,
    tray_wall_nose,
    vhb_slot,
    vhb_slot_margin,
)
from switch_plate import export, plate_outline, polygon


def nearest_vertex(sketch: Sketch, x: float, y: float):
    vertex = min(sketch.vertices(), key=lambda v: (v.center() - Vector(x, y)).length)
    assert (vertex.center() - Vector(x, y)).length < 0.01, f"no corner at {x}, {y}"
    return vertex


def filleted_polygon(corners) -> Sketch:
    """Closed polygon through [(corner, fillet radius)], like a Fusion sketch."""
    shape = polygon([xy for xy, _ in corners])
    for (x, y), r in corners:
        if r > 0:
            shape = fillet(nearest_vertex(shape, x, y), r)
    return shape


def outlines(layout):
    """Plan-view sketches: (cavity, key section outside, palm tray)."""
    inner = filleted_polygon(layout.CASE_INNER)
    outer = offset(inner, case_wall, kind=Kind.ARC)
    xs = [x for (x, _), _ in layout.CASE_INNER]
    x0, x1 = min(xs) - case_wall, max(xs) + case_wall
    free_x = layout.TRAY_EDGE_X
    wall_x = x1 if abs(free_x - x0) < abs(free_x - x1) else x0  # the tray's outer-wall side
    lo, hi = sorted((free_x, wall_x))

    # The case front is a straight face across the tray's width, filling in under the
    # key outline; it reaches well into the cavity, which the walls cut back out.
    front = Pos((lo + hi) / 2, layout.CASE_FRONT + 10) * Rectangle(hi - lo, 20)
    outer = outer + front
    outer = fillet(nearest_vertex(outer, free_x, front_corner_y(outer, free_x, layout)), tray_corner_round)
    assert len(outer.faces()) == 1, f"outline split into {len(outer.faces())} faces"

    tray = Pos((lo + hi) / 2, (layout.TRAY_FRONT + layout.CASE_FRONT) / 2) * Rectangle(
        hi - lo, layout.CASE_FRONT - layout.TRAY_FRONT
    )
    return inner, outer, tray


def front_corner_y(outer: Sketch, x: float, layout) -> float:
    """y of the convex corner where the tray's free edge meets the key outline."""
    above = [v.center().Y for v in outer.vertices() if abs(v.center().X - x) < 1e-3 and v.center().Y > layout.CASE_FRONT + 0.1]
    return min(above)


def tray_wall(x: float, layout):
    """One palm-tray side wall, case_wall thick from x, profiled in y-z: rounded nose
    at the front, coved up into the case front at the back."""
    yf, yb = layout.TRAY_FRONT, layout.CASE_FRONT
    lower = Pos((yf + yb + 1) / 2, (tray_floor - 1 + tray_wall_height) / 2) * Rectangle(
        yb + 1 - yf, tray_wall_height - tray_floor + 1
    )
    lower = fillet(nearest_vertex(lower, yf, tray_wall_height), tray_wall_nose)
    cove_h = case_height - tray_wall_height
    upper = Pos(yb + (1 - tray_wall_cove) / 2, tray_wall_height + cove_h / 2 - 0.05) * Rectangle(
        tray_wall_cove + 1, cove_h + 0.1
    )
    upper -= Pos(yb - tray_wall_cove, tray_wall_height + tray_wall_cove) * Circle(tray_wall_cove)
    profile = Plane.YZ.offset(x) * (lower + upper)
    return extrude(profile, case_wall)


def xz_rounded(x0: float, x1: float, z0: float, z1: float, r: float, depth: float):
    """A rounded rectangle in the x-z plane, extruded depth along y about y = 0."""
    sk = Plane.XZ * (Pos((x0 + x1) / 2, (z0 + z1) / 2) * RectangleRounded(x1 - x0, z1 - z0, r))
    return extrude(sk, depth / 2, both=True)


def snaps(layout, grow: float = 0.0) -> list:
    """The lid's snap bumps, as rounded bars along the case's outer wall at each of
    LID_SNAPS, reaching snap_depth into it, at mid-skirt height. grow makes them bigger
    all round (the case's dimples)."""
    _, outer, _ = outlines(layout)
    wire, face = outer.faces()[0].outer_wire(), outer.faces()[0]
    r, length, z = snap_r + grow, snap_len + 2 * grow, case_height - lid_skirt / 2
    bars = []
    for x, y in layout.LID_SNAPS:
        p = Vector(x, y, 0)
        u = min((i / 2000 for i in range(2001)), key=lambda u: (wire @ u - p).length)
        at, t = wire @ u, (wire % u).normalized()
        n = Vector(t.Y, -t.X, 0)
        if face.is_inside(at + n * 0.5):
            n = -n
        c = at + n * (snap_r - snap_depth) + Vector(0, 0, z)
        angle = math.degrees(math.atan2(t.Y, t.X))
        bar = Pos(c) * Rot(0, 0, angle) * Rot(0, 90, 0) * Cylinder(r, length)
        bar += [Pos(c + t * (length / 2 * s)) * Sphere(r) for s in (-1, 1)]
        bars.append(bar)
    return bars


def case(layout):
    inner, outer, tray = outlines(layout)

    # Floor: the key section is case_floor thick, the tray tray_floor; round the bottom edge
    floor = outer + tray
    if layout.POD_CENTER:
        floor += touchid.floor_plan(layout)
    body = extrude(floor, case_floor)
    body -= Pos(0, 0, tray_floor) * extrude(tray - outer, case_floor - tray_floor)
    # two VHB tape slots run front to back in the tray floor, at a quarter of its width in from each side
    tb = tray.bounding_box()
    w, d = vhb_slot
    length = layout.CASE_FRONT - layout.TRAY_FRONT - 2 * vhb_slot_margin
    for f in (0.25, 0.75):
        x = tb.min.X + f * (tb.max.X - tb.min.X)
        body -= Pos(x, (layout.TRAY_FRONT + layout.CASE_FRONT) / 2, tray_floor - d / 2) * Box(w, length, d)
    bottom = body.faces().sort_by(Axis.Z)[0]
    body = fillet(bottom.edges(), case_bottom_round)

    walls = Pos(0, 0, case_floor) * extrude(outer - inner, case_height - case_floor)
    body += walls
    # dimples the lid's snap bumps click into
    body -= snaps(layout, snap_dimple_clearance)
    # the USB/switch opening: through the wall from the floor up, and below the floor a
    # recess the wall's depth (outer less inner), so a fingertip reaches the switch
    (px0, py0), (px1, py1) = layout.PORT
    band = Part() + extrude(outer - inner, case_height)
    body -= band & Pos(0, (py0 + py1) / 2) * xz_rounded(px0, px1, port_recess_floor, port_top, port_round, py1 - py0)

    # Right half: fill the open floor between the thumb keys and the ball up to the rim,
    # ball_fill_gap off the plate's edge and curved round the ball holder's cup (the
    # keycap reliefs below cut it back round the caps, as they do the walls)
    if getattr(layout, "BALL_FILL_BOX", None):
        (fx0, fy0), (fx1, fy1) = layout.BALL_FILL_BOX
        bx, by, _ = layout.OUTLINE_CUTS[0]
        fill = inner & Pos((fx0 + fx1) / 2, (fy0 + fy1) / 2) * Rectangle(fx1 - fx0, fy1 - fy0)
        fill -= offset(plate_outline(layout), ball_fill_gap, kind=Kind.ARC)
        fill -= Pos(bx, by) * Circle(ball_cup_r)
        fill = Sketch() + [f for f in fill.faces() if f.area > 1.0]  # no slivers along the plate
        # round the one knife-point corner where the curve meets the plate's edge
        tip = min(fill.vertices(), key=lambda v: (v.center() - Vector(bx, by + ball_cup_r)).length)
        fill = fillet(tip, ball_fill_round)
        body += Pos(0, 0, case_floor) * extrude(fill, case_height - case_floor)

        # and in front of the ball, clear the wall band round the cup and the holder's front
        (hx0, hy0), (hx1, hy1) = layout.HOLDER_FRONT_BOX
        clear = Pos(bx, by) * Circle(ball_cup_r) + Pos((hx0 + hx1) / 2, (hy0 + hy1) / 2) * RectangleRounded(
            hx1 - hx0, hy1 - hy0, holder_front_round)
        clear &= Pos(bx, layout.CASE_FRONT + ball_front_wall + 50.0) * Rectangle(4 * ball_cup_r + 2 * (hx1 - hx0), 100.0)
        clear = Sketch() + (clear & (outer - inner)).faces()
        body -= Pos(0, 0, case_floor) * extrude(clear, case_height)

    x0, x1 = tray.bounding_box().min.X, tray.bounding_box().max.X
    body += tray_wall(x0, layout)
    body += tray_wall(x1 - case_wall, layout)

    inserts = touchid.case_inserts(layout)
    standoff_h = pcb_z - case_floor
    for x, y in inserts:
        body += Pos(x, y, case_floor + standoff_h / 2) * Cylinder(standoff_dia / 2, standoff_h)

    # The pocket runs up to the PCB, trimming the standoffs that overhang it
    for points in [layout.POCKET] + getattr(layout, "POCKETS_EXTRA", []):
        body -= Pos(0, 0, pocket_floor) * extrude(polygon(points), pcb_z - pocket_floor)
    # the battery wire's channel, its floor ramping up from the battery pocket's to the
    # Touch ID board pocket's level at the power connector, and flat on to the wall
    if getattr(layout, "POWER_RUN", None):
        x0, x1 = layout.POWER_RUN_RAMP
        xw = x1 + (50.0 if x1 > x0 else -50.0)  # past the inner wall
        run_floor = case_floor - board_pocket
        side = Plane.XZ * Polygon((x0, pocket_floor), (x1, run_floor), (xw, run_floor), (xw, pcb_z), (x0, pcb_z), align=None)
        body -= extrude(polygon(layout.POWER_RUN), pcb_z) & extrude(side, 200.0, both=True)

    for x, y in inserts:
        body -= Pos(x, y, pcb_z / 2) * Cylinder(case_shaft_hole / 2, pcb_z)
    for x, y in layout.SENSOR_SCREWS:
        body -= Pos(x, y, case_floor / 2) * Cylinder(sensor_screw_hole / 2, case_floor)
    for x, y in inserts + layout.SENSOR_SCREWS:
        body -= Pos(x, y, case_cbore_depth / 2) * Cylinder(case_cbore / 2, case_cbore_depth)
    if layout.TRACKBALL_HOLE:
        x, y = layout.TRACKBALL_HOLE
        body -= Pos(x, y, case_floor / 2) * Cylinder(trackball_hole / 2, case_floor)
    for x, y in layout.FEET:
        body -= Pos(x, y, foot_depth / 2) * Cylinder(foot_dia / 2, foot_depth)
    if layout.POD_CENTER:
        body = touchid.add(body, layout, inner)
    # wall reliefs round the keycaps, last so the pod can't fill them back in: every cap
    # gets keycap_clearance, and KEY_RELIEFS cut further where a cap still caught
    side, h = keycap + 2 * keycap_clearance, case_height + 1 - key_relief_z
    caps = Part() + [Pos(x, y, key_relief_z + h / 2) * Rot(0, 0, a) * Box(side, side, h)
                    for x, y, a in layout.KEYS + layout.THUMB_KEYS]
    # never thin the wall below min_wall where a cap sits right against the outside
    body -= Pos(0, 0, key_relief_z) * extrude(offset(outer, -min_wall, kind=Kind.ARC), h) & caps
    for (kx, ky, ka), (x0, x1, y0, y1) in getattr(layout, "KEY_RELIEFS", []):
        body -= Pos(kx, ky) * Rot(0, 0, ka) * Pos((x0 + x1) / 2, (y0 + y1) / 2, (key_relief_z + case_height + 1) / 2) * Box(
            x1 - x0, y1 - y0, case_height + 1 - key_relief_z
        )

    assert len(body.solids()) == 1, f"case split into {len(body.solids())} solids"
    return body


CASES = {"left_case": left, "right_case": right}

if __name__ == "__main__":
    for name, layout in CASES.items():
        part = case(layout)
        print(f"{name}: volume {part.volume:.1f} mm^3, bbox {part.bounding_box().size}")
        export(part, name, flip=False)
