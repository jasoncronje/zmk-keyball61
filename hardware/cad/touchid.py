"""Touch ID mod for the left case: the sensor from an Apple Magic Keyboard with Touch ID
in a pod at the thumb corner, and its logic board in a pocket in the case floor.

The pod grows out of the case front beside the palm tray, turned with the outer thumb
key. Its top is one flat face that starts at the case rim and falls toward the front
(pod_tilt), with the sensor set flush in it. Its edges follow the case's: sharp along the
top, the outer plan corner rounded like the case corners, the bottom edge rounded with
the case bottom (case.py adds floor_plan() to the floor). It covers the tray's free-side
wall where they meet, flush with that wall's tray face, so the wooden rest has a flat face
to sit against. The pod's front meets the wall's top square, with no cove.

The whole sloping face is a separate cap, printed face down, so the face comes out flat
and the sensor mount (skin, recesses, screw pilots) needs no supports. It meets the case
along the crease and along a line round the pod's sides that carries on from the tray
wall's top edge. The sensor, the puck's c-plate and our back plate hang under the cap in
an open pocket in the case; two legs from the cap reach the pocket floor and are screwed
from the case bottom. The sensor cable runs back under the rim and through a slot in the
case front wall to the board, whose Touch ID plug faces the thumb cluster. The board lies
upside down, so its pocket runs on past that end for the Touch ID and battery cables to
fold out from under it.

case.py calls add(); lid.py cuts the lid skirt clear of pod_plan(); cap() and
back_plate() are their own parts.
"""

import math

from build123d import (
    Box,
    Cylinder,
    Kind,
    Location,
    Pos,
    Rectangle,
    Rot,
    Plane,
    Sketch,
    Text,
    Vector,
    extrude,
    fillet,
    offset,
)

from params import (
    pcb_z,
    board_cable_bay,
    board_clearance,
    board_post,
    board_post_height,
    board_screw_depth,
    board_screw_pilot,
    board_pocket,
    board_post_margin,
    case_bottom_round,
    case_cbore,
    case_cbore_depth,
    case_floor,
    case_height,
    case_wall,
    fdm_hole_clearance,
    pod_round,
    pod_size,
    pod_tilt,
    screw_thread_dia,
    standoff_dia,
    tid_back_hole,
    tid_back_pad,
    tid_back_plate,
    tid_back_pocket,
    tid_pad_drop,
    tid_pad_drops,
    tid_bracket,
    tid_cap_gap,
    tid_flange,
    tid_flange_depth,
    tid_leg,
    tid_leg_gap,
    tid_leg_pilot,
    tid_leg_screw,
    tid_legs,
    tid_plate,
    tid_plate_depth,
    tid_pocket_floor,
    tid_ribbon,
    tid_channel_skin,
    tid_cable_channel,
    tid_cable_turn,
    tid_slot_reach,
    tid_roof,
    tid_screw_hole,
    tid_screw_pitch,
    tid_screw_top,
    tid_seat,
    tid_shaft,
    tid_shaft_back,
    tid_shift,
    tid_skin,
    tid_window,
    tray_wall_height,
)
from switch_plate import polygon

FAR = 100.0  # reach of the clipping shapes past the part
SINK = 12.0  # how far the pod's plan runs back (and left) into the case, which hides it


def case_inserts(layout):
    """Plate inserts that still get a case standoff and screw."""
    return [xy for i, xy in enumerate(layout.INSERTS) if i not in layout.CASE_SKIP_INSERTS]


def _crease(layout):
    """The straight line where the pod's top face leaves rim height: from the corner of
    the case front over the palm tray (where the pod's tray-side face starts) to where the
    pod's right side meets the case front wall. All of the case wall between them lies
    behind it, so the case keeps its full height, the pod is level with the rim up to the
    line, and the face falls away in front of it. Returns (start, direction in degrees)."""
    start = Vector(_clip_x(layout), layout.CASE_FRONT)
    pod = Pos(*layout.POD_CENTER) * Rot(0, 0, layout.POD_ANGLE)
    end = (pod * Pos(pod_size[0] / 2, tid_shaft_back + 1.5 - case_wall)).position  # case wall outside
    return start, math.degrees(math.atan2(end.Y - start.Y, end.X - start.X))


def _behind(layout, x: float, y: float) -> float:
    """How far (x, y) lies behind the crease, in plan; negative in front of it."""
    start, a = _crease(layout)
    t = math.radians(a)
    return -(x - start.X) * math.sin(t) + (y - start.Y) * math.cos(t)


def _face_z(layout, x: float, y: float) -> float:
    """Height of the pod top at (x, y): the sloping face in front of the crease."""
    return case_height + min(_behind(layout, x, y), 0) * math.tan(math.radians(pod_tilt))


def _above_plane(layout, depth: float = 0.0):
    """Everything above the plane of the pod's top face, lowered by depth (square to it)."""
    start, a = _crease(layout)
    return (Pos(start.X, start.Y, case_height) * Rot(0, 0, a) * Rot(pod_tilt, 0, 0)
            * Pos(0, 0, FAR / 2 - depth) * Box(2 * FAR, 2 * FAR, FAR))


def _in_front(layout, gap: float = 0.0):
    """Everything in front of the vertical plane through the crease, less gap."""
    start, a = _crease(layout)
    return Pos(start.X, start.Y) * Rot(0, 0, a) * Pos(0, -FAR / 2 - gap) * Box(2 * FAR, FAR, 2 * FAR)


def sensor_frame(layout) -> Location:
    """At the sensor centre on the pod's top face, tilted with it; local +y points back
    into the case (the mount keeps the pod's turn), local z out of the face."""
    start, a = _crease(layout)
    centre = (Pos(*layout.POD_CENTER) * Rot(0, 0, layout.POD_ANGLE) * Pos(0, -tid_shift)).position
    z = _face_z(layout, centre.X, centre.Y)
    return Pos(centre.X, centre.Y, z) * Rot(0, 0, a) * Rot(pod_tilt, 0, 0) * Rot(0, 0, layout.POD_ANGLE - a)


def _pod_shape(layout, back: float) -> Sketch:
    """Pod footprint from its front edge to `back` behind the pod centre, the outer front
    corner rounded. It runs SINK further left than the pod width, so it reaches the tray
    wall, and stops flush with that wall's inside face (a square corner there)."""
    w, d = pod_size
    frame = Pos(*layout.POD_CENTER) * Rot(0, 0, layout.POD_ANGLE)
    shape = frame * Pos(-SINK / 2, (back - d / 2) / 2) * Rectangle(w + SINK, back + d / 2)
    clip_x = _clip_x(layout)
    side = 1 if layout.TRAY_EDGE_X < 0 else -1
    shape &= Pos(clip_x + side * FAR / 2, layout.POD_CENTER[1]) * Rectangle(FAR, 2 * FAR)
    corner = (frame * Pos(w / 2, -d / 2)).position
    vertex = shape.vertices().sort_by(lambda v: (v.center() - corner).length)[0]
    assert (vertex.center() - corner).length < 0.01, f"no pod corner at {corner}"
    return fillet(vertex, pod_round)


def pod_plan(layout) -> Sketch:
    """The pod's footprint up to the case front (the lid's skirt is cut clear of it)."""
    return _pod_shape(layout, pod_size[1] / 2)


def floor_plan(layout) -> Sketch:
    """The whole pod footprint, case walls included: case.py adds it to the floor, so the
    case's bottom round runs around the pod."""
    return _pod_shape(layout, pod_size[1] / 2 + SINK)


def _clip_x(layout) -> float:
    return layout.TRAY_EDGE_X - case_wall if layout.TRAY_EDGE_X < 0 else layout.TRAY_EDGE_X + case_wall


def _front_y(layout, x: float) -> float:
    """y of the pod's front edge at x."""
    a = math.radians(layout.POD_ANGLE)
    cx, cy = layout.POD_CENTER
    # front edge: points c + t*u - d/2*v, with u = (cos a, sin a), v = (-sin a, cos a)
    t = (x - cx - pod_size[1] / 2 * math.sin(a)) / math.cos(a)
    return cy + t * math.sin(a) - pod_size[1] / 2 * math.cos(a)


def _pod_body(layout, inner: Sketch):
    """Level with the case rim up to the crease, then one flat face falling toward the
    front. It overlaps the case walls it grows out of, and stops at the cavity. It starts
    above the case's bottom round, which the floor carries around it."""
    plan = floor_plan(layout) - inner
    body = Pos(0, 0, case_bottom_round) * extrude(plan, case_height - case_bottom_round)
    return body - _above_plane(layout)


def _cap_depth(layout) -> float:
    """The cap's thickness, square to the face: its underside meets the tray wall's top
    at the pod's tray-side front corner, so the seam carries on from the wall's top edge."""
    x = _clip_x(layout)
    return (_face_z(layout, x, _front_y(layout, x)) - tray_wall_height) * math.cos(math.radians(pod_tilt))


def _cap_space(layout):
    """Where the cap is: over the pod's footprint, in front of the crease and above the
    cap's underside. The case keeps none of it."""
    return extrude(floor_plan(layout), case_height) & _in_front(layout) & _above_plane(layout, _cap_depth(layout))


def _bottom_frame(layout) -> Location:
    """Under the pod centre at the case bottom, turned like the pod."""
    return Location((*layout.POD_CENTER, 0), (0, 0, layout.POD_ANGLE))


def _leg_points(layout):
    """Where the cap's legs stand, at the case bottom (turned like the pod): under their
    spots on the back plate's face."""
    points = [(sensor_frame(layout) * Pos(u, v, -tid_seat)).position for u, v in tid_legs]
    return [Location((p.X, p.Y, 0), (0, 0, layout.POD_ANGLE)) for p in points]


def _block(u0, u1, v0, v1, z0, z1):
    return Pos((u0 + u1) / 2, (v0 + v1) / 2, (z0 + z1) / 2) * Box(u1 - u0, v1 - v0, z1 - z0)


def _layer(w, d, depth0, depth1, at=(0, 0)):
    """Block in the sensor frame from depth0 down to depth1 under the face."""
    return Pos(at[0], at[1], -(depth0 + depth1) / 2) * Box(w, d, depth1 - depth0)


def _screws():
    """The puck's back-plate screw grid (sensor frame), kept as the puck has it: the side
    with no middle screw faces the case, so the cable leaves the middle of the sensor
    straight back through it. Its back-left screw would sit behind the crease, so it is
    left out."""
    p = tid_screw_pitch
    return [(-p, -p), (0, -p), (p, -p), (-p, 0), (p, 0), (p, p)]


def cap(layout, inner: Sketch):
    """The pod's sloping top with the sensor mount under it, in place on the case."""
    part = _pod_body(layout, inner) & _in_front(layout, tid_cap_gap) & _above_plane(layout, _cap_depth(layout))
    cuts = [
        Pos(0, 0, -tid_skin / 2 + 0.5) * Cylinder(tid_window / 2, tid_skin + 1),
        _layer(*tid_flange, tid_skin, tid_flange_depth),
        _layer(tid_bracket, tid_bracket, tid_flange_depth, tid_seat),
        _layer(tid_plate, tid_plate, tid_seat, FAR),
        # the cable leaves the middle of the c-plate recess past the back plate, out the cap's back
        _layer(tid_ribbon[0], tid_shaft_back + tid_shift - tid_bracket / 2, tid_flange_depth, FAR,
               at=(0, (tid_shaft_back + tid_shift + tid_bracket / 2) / 2)),
    ]
    cuts += [Pos(x, y, -(tid_screw_top + tid_seat) / 2) * Cylinder(tid_screw_hole / 2, tid_seat - tid_screw_top)
             for x, y in _screws()]
    part -= [sensor_frame(layout) * c for c in cuts]

    # Legs from the back plate's face to just above the pocket floor, with pilots for the
    # screws from the case bottom, 1 mm past their tips
    z0 = tid_pocket_floor + tid_leg_gap
    tip = case_cbore_depth + tid_leg_screw + 1.0
    below_seat = sensor_frame(layout) * Pos(0, 0, -tid_seat - FAR / 2) * Box(2 * FAR, 2 * FAR, FAR)
    for at in _leg_points(layout):
        leg = (at * Pos(0, 0, (z0 + case_height) / 2) * Cylinder(tid_leg / 2, case_height - z0)) & below_seat
        part += leg
        part -= at * Pos(0, 0, (z0 + tip) / 2) * Cylinder(tid_leg_pilot / 2, tip - z0)
    return part


def cap_print_pose(layout) -> Location:
    """Turns the cap face down onto the bed."""
    return Rot(180, 0, 0) * sensor_frame(layout).inverse()


def back_plate(layout, drop: float = tid_pad_drop, label: bool = False):
    """The puck's back plate, remade to clear the cap's legs and the crease, in place
    under the sensor (its pocket and pad face the sensor). `drop` lowers the pad's face
    that far, to give the sensor's switch room to travel: past the pad's height the pad
    is gone and the pocket goes deeper. `label` engraves the drop on the back."""
    side, thick = tid_back_plate
    pw, pd = tid_back_pocket
    aw, ad, ah, av = tid_back_pad
    part = _layer(side, side, tid_seat, tid_seat + thick)
    part -= _layer(pw, pw, tid_seat, tid_seat + pd + max(0.0, drop - ah))
    if drop < ah:
        part += _layer(aw, ad, tid_seat + pd - ah + drop, tid_seat + pd, at=(0, av))
    if label:
        # on the front edge, between two screw holes, reading the right way round from the back
        back = Plane(origin=(-5.1, -tid_screw_pitch, -(tid_seat + thick)), x_dir=(-1, 0, 0), z_dir=(0, 0, -1))
        part -= extrude(back * Text(f"{drop:.1f}", 4.5), -0.4)
    part -= [Pos(x, y, -tid_plate_depth / 2) * Cylinder(tid_back_hole / 2, FAR) for x, y in _screws()]
    part = sensor_frame(layout) * part
    # notches round the legs, open to the plate's sides
    gap = fdm_hole_clearance / 2
    for (u, _), at in zip(tid_legs, _leg_points(layout)):
        out = math.copysign(tid_back_plate[0] / 2, u) - u
        part -= at * Cylinder(tid_leg / 2 + gap, 2 * case_height)
        part -= at * Pos(out / 2, 0) * Box(abs(out), tid_leg + 2 * gap, 2 * case_height)
    # it lowers into the pocket with the cap, clear of the rim behind the crease
    return part & _in_front(layout, tid_cap_gap)


def back_plate_set(layout):
    """Back plates with the pad lowered in steps, each labelled on its back, laid out in a
    row ready to print: try each under the sensor and keep the one that clicks best."""
    plates = []
    for i, drop in enumerate(tid_pad_drops):
        plate = back_plate_print_pose(layout) * back_plate(layout, drop, label=True)
        plates.append(Pos(i * (tid_back_plate[0] + 5), 0) * plate)
    return plates


def back_plate_print_pose(layout) -> Location:
    """Lays the back plate flat on the bed, pocket up."""
    return Pos(0, 0, tid_plate_depth) * sensor_frame(layout).inverse()


def _case_cuts(layout):
    """The pocket under the cap, the cable slot, and the counterbored holes for the cap's
    screws."""
    # centred on the back plate as it hangs under the tilted face, back to tid_shaft_back
    mid = (sensor_frame(layout) * Pos(0, 0, -(tid_seat + tid_plate_depth) / 2)).position
    du, dv, _ = (_bottom_frame(layout).inverse() * Pos(mid.X, mid.Y, 0)).position
    pocket = _block(du - tid_shaft / 2, du + tid_shaft / 2, dv - tid_shaft / 2, tid_shaft_back,
                    tid_pocket_floor, case_height - tid_roof)
    # the cable slot through the case front wall, in line with the cable's way out of the
    # cap, from the board pocket's floor up past the case floor, so the cable stays under
    # the PCB
    z0, z1 = case_floor - board_pocket, case_floor + 0.2 + tid_ribbon[1]
    v0, v1 = tid_shaft_back - 1, tid_shaft_back + tid_slot_reach
    slot = Pos(0, (v0 + v1) / 2, (z0 + z1) / 2) * Box(tid_ribbon[0], v1 - v0, z1 - z0)
    cuts = [_bottom_frame(layout) * pocket, _bottom_frame(layout) * slot - _post_skins(layout)]
    if getattr(layout, "TID_CABLE_END", None):
        cuts.append(_cable_channel(layout))
    for at in _leg_points(layout):
        cuts.append(at * Pos(0, 0, tid_pocket_floor / 2) * Cylinder((screw_thread_dia + fdm_hole_clearance) / 2, tid_pocket_floor + 0.1))
        cuts.append(at * Pos(0, 0, case_cbore_depth / 2) * Cylinder(case_cbore / 2, case_cbore_depth))
    return cuts


def _post_skins(layout):
    """The case standoffs with a skin round them, kept by the cable's cuts."""
    r = standoff_dia / 2 + tid_channel_skin
    return [Pos(x, y, pcb_z / 2) * Cylinder(r, pcb_z) for x, y in case_inserts(layout)]


def _cable_channel(layout):
    """Floor channel at the board pocket's depth, open to the PCB, from the slot's turn to
    TID_CABLE_END under the board, clear of the case standoffs."""
    start = (_bottom_frame(layout) * Pos(0, tid_shaft_back + tid_cable_turn)).position
    end = Vector(*layout.TID_CABLE_END)
    d = end - Vector(start.X, start.Y)
    z0 = case_floor - board_pocket
    h = pcb_z - z0
    mid = Pos((start.X + end.X) / 2, (start.Y + end.Y) / 2, z0 + h / 2)
    run = mid * Rot(0, 0, math.degrees(math.atan2(d.Y, d.X))) * Box(d.length, tid_cable_channel, h)
    ends = [Pos(p.X, p.Y, z0 + h / 2) * Cylinder(tid_cable_channel / 2, h) for p in (start, end)]
    return run + ends - _post_skins(layout)


def board_place(layout, shape):
    x, y, a = layout.BOARD_POSE
    return Pos(x, y) * Rot(0, 0, a) * shape


def board_point(layout, xy) -> Vector:
    return board_place(layout, Pos(*xy)).position


def _board_space(layout, grow: float) -> Sketch:
    """The board's outline plus the cable bay past its connector end (board frame), grown
    by `grow`."""
    x0, x1, y1 = layout.BOARD_CABLE_BAY
    bay = Pos((x0 + x1) / 2, (y1 - board_cable_bay) / 2) * Rectangle(x1 - x0, y1 + board_cable_bay)
    return offset(polygon(layout.BOARD_OUTLINE) + bay, grow, kind=Kind.ARC)


def board_pocket_cut(layout):
    z0 = case_floor - board_pocket
    cut = board_place(layout, Pos(0, 0, z0) * extrude(_board_space(layout, board_clearance), board_pocket + 0.01))
    # the bay steps round the case standoffs, so they keep floor round their feet
    r = standoff_dia / 2 + board_post_margin
    return cut - [Pos(x, y, case_floor) * Cylinder(r, 2 * case_floor) for x, y in case_inserts(layout)]


def board_posts(layout):
    z0 = case_floor - board_pocket
    return [Pos(board_point(layout, xy).X, board_point(layout, xy).Y, z0 + board_post_height / 2)
            * Cylinder(board_post / 2, board_post_height) for xy in layout.BOARD_HOLES]


def board_screw_holes(layout):
    top = case_floor - board_pocket + board_post_height
    return [Pos(board_point(layout, xy).X, board_point(layout, xy).Y, top - board_screw_depth / 2)
            * Cylinder(board_screw_pilot / 2, board_screw_depth + 0.01) for xy in layout.BOARD_HOLES]


def pod_test(body, layout):
    """The corner of the finished case round the pod, with a stub of the tray wall in
    front and a strip of the case behind the crease: tries the cap's fit and seams, its
    screws from below and the cable's way into the case before the whole case is printed.
    Prints bottom down, like the case."""
    return body & (_bottom_frame(layout) * _block(-25, 17, -24, 26, 0, case_height))


def board_coupon(body, layout):
    """The case floor round the logic-board pocket, its cable bay and its pins, cut down to
    a slab, to try the board and fold its cables out. Prints bottom down."""
    rim, under = 4.0, 1.2
    z0 = case_floor - board_pocket - under
    slab = board_place(layout, Pos(0, 0, z0) * extrude(_board_space(layout, board_clearance + rim), case_floor - z0))
    return Pos(0, 0, -z0) * (body & slab)


def lightning_test(body, layout):
    """The case floor round the board's connector end (out to its first pin), the cable bay,
    the Lightning ear strip and the plug channel into the controller pocket, with the stub of
    inner wall beside them, cut off just above the PCB: tries the folded receptacle and the
    cut cable's plug before the whole case is printed. Prints bottom down, like the case."""
    top = pcb_z + 1
    board_end = Pos(-57.0, -2.0, top / 2) * Box(26, 40, top)  # x -70..-44, the board's end and pin
    bay = Pos(-33.0, 10.0, top / 2) * Box(22, 64, top)  # x -44..-22, y -22..42
    return body & (board_end + bay)


def lightning_pocket_cut(layout):
    """Floor pockets for the Lightning receptacle's ears and the cut cable's plug, open up to
    the PCB."""
    cut = []
    for (x0, y0, x1, y1), z in layout.LIGHTNING_POCKET:
        cut.append(Pos((x0 + x1) / 2, (y0 + y1) / 2, (z + pcb_z) / 2) * Box(x1 - x0, y1 - y0, pcb_z - z))
    return cut


def add(body, layout, inner: Sketch):
    """The left case plus its share of the pod, the pocket under the cap, the cable slot
    the board pocket and the Lightning pocket."""
    body += _pod_body(layout, inner)
    body -= _cap_space(layout)  # with the tray wall's end inside the pod
    body -= _case_cuts(layout)
    body -= board_pocket_cut(layout)
    if getattr(layout, "LIGHTNING_POCKET", None):
        body -= lightning_pocket_cut(layout)
    body += board_posts(layout)
    body -= board_screw_holes(layout)
    return body
