"""Right-half switch plate layout (trackball side).

Frame: looking down at the plate's top (switch side), z = 0 on the bottom face.
Numbers were measured from `Switch Plates/Plates_v2_MX_Right.3mf`, which Fusion
exported upside down (print orientation), so x here is the negated export x.
"""

from params import outline_inset

UNIT_SPACING = 19.0375  # measured key pitch; the left plate measures 19.0077

# (x, y, rotation in degrees) of each switch centre
KEYS = [
    (53.176, 62.425, 0),
    (53.176, 43.388, 0),
    (53.176, 24.350, 0),
    (53.176, 5.313, 0),
    (72.213, 64.924, 0),
    (72.213, 45.886, 0),
    (72.213, 26.848, 0),
    (72.213, 7.811, 0),
    (91.251, 67.422, 0),
    (91.251, 48.384, 0),
    (91.251, 29.347, 0),
    (91.251, 10.309, 0),
    (110.288, 62.725, 0),
    (110.288, 43.687, 0),
    (110.288, 24.650, 0),
    (110.288, 5.612, 0),
    (129.326, 55.729, 0),
    (129.326, 36.692, 0),
    (129.326, 17.655, 0),
    (129.326, -1.383, 0),
    (129.326, -20.420, 0),
    # outer column (pinky)
    (148.363, 55.729, 0),
    (148.363, 36.692, 0),
    (148.363, 17.655, 0),
    (148.363, -1.383, 0),
    (148.363, -20.420, 0),
]

# Keys whose outline comes from WEBS instead of their 1u square
THUMB_KEYS = [
    (34.138, 1.815, 0),
    (46.753, -20.046, 10),
    (26.019, -25.512, 20),
]

# Bottom edge of the inner column's last key. A web edge that is only nearly on a
# grid edge leaves a sliver that breaks the fillets, so it is computed, not measured.
INNER_COLUMN_BOTTOM = 5.313 - (UNIT_SPACING / 2 - outline_inset)

# Solid webs, sharp corners (rounded later with the rest of the outline). Points
# that sit inside the key grid only join the web to it.
WEBS = [
    [
        (45.000, 11.332),  # inside the grid
        (25.122, 11.332),
        (25.122, -6.705),
        (25.453, -16.199),
        (14.553, -20.166),
        (20.672, -36.977),
        (37.949, -30.689),
        (57.117, -27.302),
        (53.996, -9.513),
        (54.244, INNER_COLUMN_BOTTOM),
        (61.850, INNER_COLUMN_BOTTOM),
        (63.287, -2.207),
        # strip under the inner columns; the trackball cutout bites into it
        (100.461, -2.207),
        (100.461, -4.706),
        (119.058, -4.706),
        (119.058, -29.439),
        (121.000, -29.439),  # inside the grid from here on
        (121.000, 0.000),
        (45.000, 0.000),
    ],
]

# Areas trimmed off the key grid before the webs are added. The slanted step from
# the inner column down to the strip cuts across the corner of its last key; the
# trim stops 0.01 mm short of the slant so the web, not the trim, forms the edge.
GRID_TRIMS = [
    [(61.076, -4.500), (62.584, -2.926), (62.800, -2.926), (62.800, -4.500)],
]

# Outline corners with a bigger fillet than params.outline_round: ((x, y), radius)
CORNER_FILLETS = [
    ((44.157, 11.332), 4.0),  # thumb web meets the inner column
    ((25.453, -16.199), 3.0),
    ((37.949, -30.689), 6.0),  # between thumb keys
    ((57.117, -27.302), 2.0),
    ((53.996, -9.513), 6.0),
    ((54.244, -3.707), 3.0),
    ((61.850, -3.707), 2.0),  # step down to the inner-column strip
    ((63.287, -2.207), 2.0),
    ((119.058, -4.706), 8.0),
]

# Circles cut out of the outline: (x, y, radius)
OUTLINE_CUTS = [
    (86.598, -18.746, 17.477),  # trackball: 34 mm ball + clearance
]

# Heat-set insert pilots, drilled up from the bottom face
INSERTS = [
    (29.135, -12.302),
    (36.979, -24.991),
    (62.277, 14.832),
    (63.113, 55.405),
    (100.702, 53.095),
    (101.188, 15.131),
    (138.844, -10.902),
    (138.844, 46.211),
]

# --- Bottom case (Cases/Cases_v3.3mf, body 3) ---

# Inside face of the case wall: (corner, fillet radius). Convex corners are r 1.5 and
# concave r 0.5; the outside face is this offset by the wall.
CASE_INNER = [
    ((62.791, 72.017), 0.5),
    ((23.437, 72.017), 1.5),
    ((23.437, 11.400), 1.5),
    ((24.807, 10.828), 0.5),
    ((24.807, -15.908), 2.5),
    ((13.804, -19.913), 1.5),
    ((20.311, -37.792), 1.5),
    ((38.145, -31.301), 2.75),
    ((57.364, -27.904), 2.75),
    ((76.368, -27.815), 3.75),
    ((86.697, -29.807), 4.25),
    ((157.974, -29.807), 1.5),
    ((157.974, 65.316), 1.5),
    ((119.988, 65.316), 0.5),
    ((119.988, 72.314), 1.5),
    ((100.966, 72.314), 0.5),
    ((100.966, 76.971), 1.5),
    ((81.814, 76.971), 1.5),
    ((81.814, 74.523), 0.5),
    ((62.791, 74.523), 1.5),
]

CASE_FRONT = -37.807  # front face of the key section, where the palm tray starts
TRAY_EDGE_X = 54.370  # the tray's free side; its other side continues the outer wall
TRAY_FRONT = -118.807

# Battery (42 x 52 at the outer wall), cut into the floor
POCKET = [(157.974, -8.269), (157.974, 43.731), (115.974, 43.731), (115.974, -8.269)]
# The battery wire's channel: it leaves the battery where the v3 print's straight one did
# and angles down to the PCB's power connector, whose plug sits 45 to 55 below the inside
# of the top wall (y 72.017), and runs on to the inner wall there. Its floor ramps from the
# battery pocket's up to power_run_floor at the connector (x from, x to)
POWER_RUN = [
    (115.974, 43.731),
    (43.437, 27.017),
    (23.437, 27.017),
    (23.437, 17.017),
    (43.437, 17.017),
    (115.974, 35.731),
]
POWER_RUN_RAMP = (115.974, 43.437)
# The controller (MCU) area, as in the v3 print
POCKETS_EXTRA = [
    [(23.437, 35.731), (43.437, 35.731), (43.437, 68.731), (23.437, 68.731)],
]

# opening in the inner top wall, plan-view box: 14 wide, centred on the USB-C and switch
# (fits a 12.5 mm plug with 0.75 per side; the v3 print had 18.6)
PORT = ((27.150, 70.0), (41.150, 80.0))
FEET = [(29.801, 65.653), (151.688, 58.952), (62.734, -110.443), (151.610, -110.443)]
# lid snaps: points on the case's outer wall, clear of the port, palm tray and pod
LID_SNAPS = [(160.0, 35.0), (160.0, -15.0), (21.4, 40.0), (52.0, 74.0), (139.0, 67.3)]

# the case is filled up to the plate top inside this box, outside the plate and the ball cup
BALL_FILL_BOX = ((50.0, -45.0), (86.598, -1.0))
# the holder's front, measured off a photo of it fitted (its front edge ~34.2 ahead of
# the ball's centre, its right end ~122): cut clear of it in the wall band
HOLDER_FRONT_BOX = ((95.0, -35.5), (123.5, -25.0))
TRACKBALL_HOLE = (86.743, -18.630)  # the plate's ball cutout is centred at 86.598, -18.746
SENSOR_SCREWS = [(96.725, -26.616), (96.725, -10.644)]

# --- Dust lid ---

# The ball holder stands to the right of the ball, over the lid. Right of the ball's
# centre the lid is open over what the plate leaves uncovered inside this box.
LID_HOLDER_BOX = ((86.598, -60.0), (119.058, 10.0))


# --- Touch ID ---

CASE_SKIP_INSERTS = []
POD_CENTER = None
