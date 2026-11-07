"""Left-half switch plate layout.

Frame: looking down at the plate's top (switch side), z = 0 on the bottom face.
Numbers were measured from `Switch Plates/SwitchPlates_BottomScrew_v2_1.3mf`, which
Fusion exported upside down (print orientation), so x here is the negated export x.
"""

UNIT_SPACING = 19.0077  # measured key pitch (not the 19.05 nominal)

# (x, y, rotation in degrees) of each switch centre
KEYS = [
    # outer column (pinky)
    (-149.641, 55.081, 0),
    (-149.641, 36.073, 0),
    (-149.641, 17.066, 0),
    (-149.641, -1.942, 0),
    (-149.641, -20.950, 0),
    (-130.633, 55.081, 0),
    (-130.633, 36.073, 0),
    (-130.633, 17.066, 0),
    (-130.633, -1.942, 0),
    (-130.633, -20.950, 0),
    (-111.626, 62.066, 0),
    (-111.626, 43.058, 0),
    (-111.626, 24.050, 0),
    (-111.626, 5.042, 0),
    (-111.626, -13.966, 0),
    (-92.618, 66.755, 0),
    (-92.618, 47.747, 0),
    (-92.618, 28.740, 0),
    (-92.618, 9.732, 0),
    (-92.618, -9.276, 0),
    (-73.610, 64.261, 0),
    (-73.610, 45.253, 0),
    (-73.610, 26.245, 0),
    (-73.610, 7.237, 0),
    (-54.602, 61.766, 0),
    (-54.602, 42.759, 0),
    (-54.602, 23.751, 0),
    (-54.602, 4.743, 0),
]

# Keys whose outline comes from WEBS instead of their 1u square
THUMB_KEYS = [
    (-69.198, -19.045, 0),
    (-47.863, -20.824, -10),
    (-35.595, 1.251, 0),
    (-27.160, -26.282, -20),
]

# Solid web around the thumb cluster, sharp corners (rounded later with the rest
# of the outline). The first point and last three overlap the main grid to join it;
# edges that only touch the grid leave slivers that break the corner fillets.
WEBS = [[
    (-46.000, 10.753),
    (-26.593, 10.753),
    (-26.593, -3.738),
    (-26.523, -11.564),
    (-26.523, -17.010),
    (-15.713, -20.944),
    (-21.822, -37.730),
    (-39.072, -31.451),
    (-58.211, -28.069),
    (-78.130, -27.976),
    (-78.130, -10.871),
    (-78.122, -7.697),
    (-83.613, -7.684),
    (-83.613, -18.281),
    (-92.000, -18.281),
    (-92.000, 0.000),
    (-46.000, 0.000),
]]

GRID_TRIMS = []  # polygons trimmed off the key grid before the webs are added
OUTLINE_CUTS = []  # circles cut out of the outline: (x, y, radius)

# Outline corners with a bigger fillet than params.outline_round: ((x, y), radius)
CORNER_FILLETS = [
    ((-45.598, 10.753), 4.0),  # thumb web meets the inner column
    ((-26.523, -17.010), 3.0),
    ((-39.072, -31.451), 3.0),  # between thumb keys
    ((-58.211, -28.069), 3.0),
]

# Heat-set insert pilots, drilled up from the bottom face
INSERTS = [
    (-140.137, -11.446),
    (-140.137, 45.578),
    (-102.104, -2.775),
    (-102.104, 54.275),
    (-64.224, 15.776),
    (-64.224, 53.876),
    (-58.643, -21.230),
    (-38.103, -25.762),
    (-30.271, -13.093),
]

# --- Bottom case (Cases/Cases_v3.3mf, body 1) ---

# Keycaps the walls crowd: the case wall is cut back round them from key_relief_z up.
# (key (x, y, rotation), (x0, x1, y0, y1) in that key's frame). The outer thumb key's walls
# stood 0.6 mm off an 18 mm cap (less at the corner rounds) and it rubbed: 0.8 more at the
# side and back (wall 2.0 -> 1.2), 0.4 at the front (1.5 -> 1.1, the Touch ID shaft is behind),
# and on past the front-left corner, where the wall bends toward the next thumb key
KEY_RELIEFS = [((-27.160, -26.282, -20), (-11.0, 10.45, -10.1, 10.3))]

# Inside face of the case wall: (corner, fillet radius). Convex corners are r 1.5 and
# concave r 0.5; the outside face is this offset by the wall.
CASE_INNER = [
    ((-121.036, -30.681), 1.5),
    ((-121.036, -23.761), 0.5),
    ((-101.974, -23.761), 1.5),
    ((-101.974, -19.146), 0.5),
    ((-79.224, -19.146), 0.5),
    ((-79.224, -28.678), 1.5),
    ((-58.521, -28.775), 2.75),
    ((-39.296, -32.173), 2.75),
    ((-21.410, -38.683), 1.5),
    ((-14.856, -20.677), 1.5),
    ((-25.865, -16.670), 2.5),
    ((-25.865, 9.999), 0.5),
    ((-24.507, 10.567), 1.5),
    ((-24.507, 71.386), 1.5),
    ((-63.863, 71.386), 0.5),
    ((-63.863, 73.900), 1.5),
    ((-82.908, 73.900), 0.5),
    ((-82.908, 76.327), 1.5),
    ((-102.246, 76.327), 1.5),
    ((-102.246, 71.682), 0.5),
    ((-121.289, 71.682), 1.5),
    ((-121.289, 64.673), 0.5),
    ((-159.292, 64.673), 1.5),
    ((-159.292, -30.681), 1.5),
]

CASE_FRONT = -38.535  # front face of the key section, where the palm tray starts
TRAY_EDGE_X = -55.653  # the tray's free side; its other side continues the outer wall
TRAY_FRONT = -119.681

# Battery (42 x 52 at the outer wall), cut into the floor
POCKET = [(-159.292, -9.031), (-117.292, -9.031), (-117.292, 42.969), (-159.292, 42.969)]
# The battery wire's channel: it leaves the battery where the v3 print's straight one did
# and angles down to the PCB's power connector, whose plug sits 45 to 55 below the inside
# of the top wall (y 71.386), and runs on to the inner wall there. Its floor ramps from the
# battery pocket's up to power_run_floor at the connector (x from, x to)
POWER_RUN = [
    (-117.292, 34.969),
    (-44.507, 16.386),
    (-24.507, 16.386),
    (-24.507, 26.386),
    (-44.507, 26.386),
    (-117.292, 42.969),
]
POWER_RUN_RAMP = (-117.292, -44.507)
# The controller (MCU) area, as in the v3 print; the Lightning plug channel joins it to the
# connector end of the battery channel
POCKETS_EXTRA = [
    [(-44.507, 34.969), (-24.507, 34.969), (-24.507, 67.969), (-44.507, 67.969)],
]

# opening in the inner top wall, plan-view box: 14 wide, centred on the USB-C and switch
# (fits a 12.5 mm plug with 0.75 per side; the v3 print had 20)
PORT = ((-41.507, 69.741), (-27.507, 80.0))
FEET = [(-30.871, 65.022), (-152.928, 58.309), (-64.018, -111.317), (-152.928, -111.317)]
# lid snaps: points on the case's outer wall, clear of the port, palm tray and pod
LID_SNAPS = [(-161.3, 35.0), (-161.3, -15.0), (-22.5, 40.0), (-53.0, 73.4), (-140.0, 66.7)]

TRACKBALL_HOLE = None
SENSOR_SCREWS = []
LID_HOLDER_BOX = None


# --- Touch ID (touchid.py) ---

# Posts the Touch ID board needs the floor space of (indices into INSERTS); the plate
# keeps its insert, it just has no screw there.
CASE_SKIP_INSERTS = [2]

# Logic board outline in its own frame (x across, y from the connector end at 0), its
# holes and the Touch ID and battery plugs; placed by BOARD_POSE (x, y, rotation in degrees)
BOARD_OUTLINE = [(0, 0), (22.21, 0), (22.21, 5.75), (26, 5.75), (26, 71.84), (30, 71.84), (30, 77), (0, 77)]
BOARD_HOLES = [(10.8, 24.7), (10.6, 74.5)]
BOARD_TOUCHID_PLUG = (20.4, 2.8)
BOARD_BATTERY_PLUG = (3.4, 4.8)
# The board lies upside down in its pocket, and both its cables plug in at the connector
# end, so the pocket runs on past that end, and over the outline's step beside the Touch ID
# plug, for them to fold out from under it: x from, x to, back to y
BOARD_CABLE_BAY = (0.0, 26.0, 5.75)
BOARD_POSE = (-37.5, -16.0, 90)

# Lightning receptacle (on the board's ribbon, folded under the board's connector end) and the
# cut cable's plug, which feeds it 5 V from the boost in the controller pocket. Measured: the
# section sticks out 6.5 past the board end, ears 18.5 across with their outer face 31 from the
# board's left edge, plug boot 14.5 past the ears. The receptacle floats; these clear it:
# ((x0, y0, x1, y1), floor z), design frame
LIGHTNING_POCKET = [
    ((-44.0, 9.0, -26.0, 15.5), 3.8),  # the ears, level with the cable bay the section lies in
    ((-26.0, 10.8, -24.6, 15.5), 3.8),  # the ear's tip, up to the inner wall where it steps out
    ((-39.0, 15.0, -29.5, 35.5), 1.5),  # the plug boot, back into the controller pocket
]

# The Touch ID cable's way from the slot in the case front to the board's plug: it turns off
# the slot, goes between case posts 5 and 6 (midway, 7.5 mm clear) and ends under the
# board, design frame
TID_CABLE_END = (-38.6, -14.7)

# Sensor pod, turned with the outer thumb key (-20 degrees, like the case front beside
# it). The sensor centre is placed so the pod's right side continues the case's right
# side (both at 70 degrees), and the sensor shaft leaves 1.5 mm of the case front wall.
POD_ANGLE = -20.0


def _pod_center():
    import math

    from params import case_wall, pod_size, tid_shaft_back

    a = math.radians(POD_ANGLE)
    u = (math.cos(a), math.sin(a))  # across the pod, to the right
    v = (-u[1], u[0])  # back, into the case
    side = (-21.410, -38.683)  # inside corners: front-right of the case ...
    front = (-39.296, -32.173)  # ... and the front corner left of it
    # u.c = u.side + wall - half the pod width;  v.c = v.front - shaft back - 1.5
    a1 = u[0] * side[0] + u[1] * side[1] + case_wall - pod_size[0] / 2
    b1 = v[0] * front[0] + v[1] * front[1] - tid_shaft_back - 1.5
    return (a1 * u[0] + b1 * v[0], a1 * u[1] + b1 * v[1])


POD_CENTER = _pod_center()
