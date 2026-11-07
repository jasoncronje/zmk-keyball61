"""Shared Keyball61 parameters (mm).

Values come from the Fusion user-parameter export `Switch Plates/switchPlateParams.csv`
(the current bottom-screw plates). Names mirror the Fusion names in snake_case.
"""

# Hardware, measured
screw_head_dia = 3.78  # M2 SHCS head
screw_head_height = 2.0
screw_thread_dia = 1.92
pcb_thick = 1.6

# Cherry MX
switch_spec = 14.0  # nominal plate cutout
relief_spec = 15.6  # switch housing width below the clips
# key pitch is per half (layout_*.UNIT_SPACING): the two printed plates differ

# FDM clearances (diametric)
fdm_hole_clearance = 0.5
fdm_square_clearance = 0.1
fdm_relief_clearance = 0.2

# Switch plate
plate_thick = 5.0
clip_ledge = 1.4  # top layer the switch clips grab; the v2 print has 1.4, the CSV still says 1.5
relief_depth = plate_thick - clip_ledge
switch_cutout = switch_spec + fdm_square_clearance  # 14.1
body_relief = relief_spec + fdm_relief_clearance  # 15.8

# Heat-set inserts (M2 x 3 mm); FDM shrink gives the interference fit
insert_d1 = 3.0
insert_length = 3.0
fdm_insert_clearance = 0.0
insert_pilot = insert_d1 + fdm_insert_clearance
insert_depth = insert_length + 0.5
insert_ceiling = plate_thick - insert_depth
insert_boss_dia = 4.2  # relief pockets stop short of this ring so inserts keep a wall

# Plate outline
outline_inset = 0.5  # outline sits this far inside the 1u key squares
outline_round = 1.0  # fillet radius on every outline corner, convex and concave

# Bottom case (from the v3 print and CAD Sources/keyball61_{battery,case_screw}_params.csv)
case_wall = 2.0
case_height = 22.0
case_floor = 7.0  # baseThickness
case_bottom_round = 2.0  # fillet on every bottom outside edge
pcb_z = 9.5  # standoff tops: the PCB sits here, the plate on the PCB
key_relief_z = 16.5  # wall reliefs round keycaps start here, just over the plate's top (16.1)
keycap = 18.0  # 1u keycap at its base
keycap_clearance = 1.0  # the walls stand at least this far off every keycap, from key_relief_z up
min_wall = 1.0  # ...but the clearance cut never leaves the wall thinner than this
standoff_dia = 6.2
battery_thick = 5.0  # 504050 LiPo
fdm_pocket_clearance = 0.5
battery_pocket = battery_thick + fdm_pocket_clearance  # 5.5 deep, under the battery, MCU and wiring
pocket_floor = case_floor - battery_pocket  # 1.5
case_shaft_hole = 2.2  # the v3 print has 2.2; the CSV derives 2.42
case_cbore = screw_head_dia + fdm_hole_clearance  # 4.28, screw heads sit flush with the bottom
case_cbore_depth = screw_head_height
foot_dia = 10.0  # stick-on feet, recessed
foot_depth = 1.0
port_top = 19.0  # USB/TRRS opening in the inner top wall runs from the floor to here
port_recess_floor = 2.5  # below the floor, the opening carries on down as a recess the wall's
# depth into the outside, so a fingertip gets under the tiny power switch
port_round = 2.0  # corner radius of the opening, seen from outside

# Palm-rest tray in front of the keys (the wooden rest sits on it)
tray_floor = 4.0
tray_wall_height = 13.0
tray_wall_nose = 9.0  # radius rounding the front of each side wall
tray_wall_cove = 8.5  # radius blending each side wall up into the case front
tray_corner_round = 6.0  # plan-view fillet where the tray's free edge meets the case
vhb_slot = (13.2, 0.9)  # width, depth: two recesses in the tray floor for 12.6 x 1.0 VHB tape,
# shallower than the tape so it stands ~0.1 proud and the wooden rest squeezes it flat
vhb_slot_margin = 8.0  # each slot's ends stop this far short of the tray front and the case front

# TPU foam-lattice palm rest (palm_rest.py), replacing the wooden one in the tray: the
# same block (100 wide, 79 deep, 20 tall at the back), its top curving down to the front
palm_rest_size = (100.0, 79.0)  # across, front to back
palm_rest_back = 20.0  # height at the back, against the case front
palm_rest_front = 8.0  # height at the front edge, estimated off the product photo
palm_rest_slope = 0.6  # the top's fall per mm at the front edge (flat at the back)
palm_rest_floor = 1.2  # solid bottom, 6 layers at 0.2
# The block is filled with a 3D Voronoi web of round struts, closed into a web over every
# outside face: bigger cells or thinner struts make it softer
palm_rest_cell = 8.0  # typical cell size (seed spacing)
palm_rest_strut = 1.6  # strut diameter, 4 lines at 0.4
palm_rest_stretch = 1.4  # cells drawn this much taller than wide, so struts lean steeper (fewer flat bridges)
palm_rest_seed = 61  # random seed for the web: change it for a different pattern

# Trackball (right half)
trackball_hole = 12.0  # through the floor under the ball
sensor_screw_hole = 2.5
# Left of the ball the case is filled from the floor to the rim, round the ball
# holder's cup: the 34 mm ball plus 3.5 (the user puts the ball's edge ~50 mm from the
# plate's bottom-right notch edge, and wants at least 3 more for the cup)
ball_cup_r = 20.5
ball_fill_gap = 0.5  # between the fill and the switch plate's edge
ball_fill_round = 2.0  # the one sharp corner, where its curve meets the plate's edge
# In front of the ball the wall band (plate edge to case front) is cut down to the floor
# round the ball's cup and the holder's front, leaving this much of the front wall
ball_front_wall = 1.2
holder_front_round = 4.0
# Ball holder housing (ball_cup.py)
ball_d = 34.0
ball_center_z = 26.5  # the user measured 9.5 from the case bottom up through the floor hole to the ball (old 7 mm floor)
# Sensor board (user's sketch + photo): stands upright on the case floor, right of the
# ball, centred on its y, lens facing -x at the ball
sensor_board_w = 22.0  # along y
sensor_board_h = 25.0
sensor_board_t = 1.6
sensor_stack = 7.12  # board back to lens front, board included
sensor_notch_w = 8.6  # the sensor body's notch in the board's top edge, centred (6.7 in from each side)
sensor_notch_h = 25.0 - 9.3  # from the top edge down to 9.3 above the floor
sensor_lens_z = 17.0  # lens opening above the board bottom, scaled off the photo (~z 24, 8 deg below the ball's centre)
sensor_lift = 0.0  # raise the board inside the housing if tracking needs the lens nearer the ball's centre
sensor_lens_gap = 2.4  # lens face to the ball: PixArt's usual focus, to be found by test prints
sensor_y_shift = 0.8  # board sits this far behind the ball's centre line, so the cover clears the lid's front strip
# Cup: a spherical shell round the ball, open toward the thumb (front-left) under one
# tilted cut, three static bearings (Si3N4 balls) pressed in a third of the way round
bearing_d = 2.5  # the common size for 34 mm balls; the user's old cup had 3 of a similar size
bearing_fit = 0.0  # pocket over the bearing's diameter (printed holes shrink, so 0 presses)
bearing_drop = 40.0  # degrees below the ball's middle
bearing_az = (105.0, 345.0, 45.0)  # degrees from +x: the opening's far side and 120 either way, clear of the low lip
ball_gap = 0.8  # ball to the shell: how far the bearings stand proud
cup_wall = 1.8  # keeps the shell 0.7 inside the plate's cutout at the plate top
# The lip, after the roBa holder (kumamuk-git/roBa case/trackballcase.stl, CC BY 4.0, from
# kepeo's Keyball Trackball Case): its inner edge fitted to planes round our ball's centre.
# A band round the back and right under a tilted top, high over the sensor and lower at
# the back; open toward the thumb and front down to a low lip, the two joined by steep
# ends at cup_arms. Each plane is (azimuth of its highest point, elevation there, elevation
# opposite), degrees above the ball's middle; both fit roBa to within ~1 and ~2 degrees
cup_top = (355.4, 54.9, 32.1)
cup_low = (263.0, -32.3, -67.3)
cup_arms = (155.0, 319.0)  # back arm, front arm: roBa's steep ends
cup_arm_round = (2.5, 4.0)  # the arm ends' top and bottom corners, near roBa's (2.5 is the most the top takes)
cup_round = 0.8  # every edge of the shell
# The keycaps round the cup, as MX caps swept through their travel: an 18 square base from
# key_press_low (pressed) to key_rest_low (at rest), tapering to keycap_top square at
# key_top. Estimates for a typical profile, not measured; the old cup and roBa stand solid
# where the key behind the ball is, so the real cap clears at least this
key_press_low = 18.5  # ~2.4 over the plate's top
key_rest_low = 22.6  # 4 mm travel over that
key_top = 31.6
keycap_top = 13.0
key_gap = 0.3  # the cup's outside off a keycap
key_patch = 0.3  # behind a keycap shave the wall thickens toward the ball (ball_gap 0.8 left 0.5)
cup_foot_r = 14.0  # foot ring on the floor, under the plate (cutout 17.5)
cup_foot_top = 11.0
cup_screw_pilot = 1.6  # M2 self-tapping, up from the case bottom
cup_screw_boss = 6.0
# Sensor cover: a rounded hood slid down over the board onto a boss on the cup's tab
cover_wall = 1.2
cover_clearance = 0.3  # board to cover, each side
cover_fit = 0.15  # cover over its boss, each side
cover_round = 3.0  # every outside edge, so a finger meets no hard corner; inside, 1.8 still clears the board's back corners
cover_top = 34.6  # flush with the lid top
tab_top = 9.0
boss_top = 11.0

# Dust lid (sits on the case rim; drawn after Top Cases:Covers/LeftTopCase_v5 and
# RightTopCase_v1, which were made for the larger v2 case)
lid_clearance = 0.3  # skirt to case outside, per side (the old lids had 0.15 on v2)
lid_wall = 1.6
lid_top = 1.6
lid_band = 11.0  # height the lid adds above the case rim, under the top: keycaps stand 9.4 over it
lid_height = case_height + lid_band + lid_top  # 34.6
lid_skirt = 6.0  # the skirt reaches this far down the case walls from the rim, enough to locate it
lid_round = 6.0  # the top rolls over into the sides on this radius
lid_seat = 4.0  # inside, the lid stands on the rim and flares out at 45 degrees over this reach
lid_ball_clearance = 2.0  # the lid's opening round the ball, past the plate's cutout radius (17.5): ~2.5 to a 34 mm ball; 1.0 still rubbed the fitted ball
# Snaps: rounded bumps inside the lid's skirt click into dimples in the case's outer wall
snap_r = 1.5  # radius of the bump's rounded ridge
snap_len = 8.0  # length of its straight part, along the wall
snap_depth = 0.4  # how far the bump reaches into the case wall
snap_dimple_clearance = 0.05  # the dimple is this much bigger all round
test_ring_skirt = 5.0  # fit-test ring: this much skirt under a lid_top-thick band

# Touch ID (left half): the sensor from an Apple Magic Keyboard sits in a pod at the
# thumb corner, its logic board in a pocket in the case floor (see touchid.py).
# The sensor mount copies the Printables puck the user printed: the puck's back plate
# clamps the sensor and its c-plate up against a thin skin with M1.2 screws. Here that
# mount lives in a cap that is the pod's whole sloping top, printed face down.
# Depths are measured down from the pod top.
tid_skin = 0.4  # over the sensor flange
tid_window = 10.6  # opening for the sensor button
tid_flange = (14.5, 15.0)  # flange recess (across, front-to-back), tid_skin down to tid_flange_depth
tid_flange_depth = 1.4
tid_bracket = 17.2  # square recess for the sensor's c-plate, down to tid_seat
tid_seat = 2.8  # the back plate presses up against this face
tid_plate = 25.2  # back-plate pocket
tid_plate_depth = 5.4  # bottom of the back plate
tid_screw_pitch = 10.25  # back-plate screw grid
tid_screw_hole = 1.3  # M1.2 pilots, from tid_screw_top down
tid_screw_top = 1.0
tid_shift = 1.9  # the sensor sits this far in front of the pod centre, so the mount clears the crease
tid_shaft = 25.6  # pocket in the case under the cap, round the back plate: this wide ...
tid_shaft_back = 14.8  # ... and to this far behind the pod centre, leaving the cable room behind the plate
tid_pocket_floor = screw_head_height + 1.0  # the pocket floor, over the cap screws' counterbores
tid_cap_gap = 0.15  # between the cap and the case where they face each other
# Back plate (the puck's, remade): 24.2 square (see below), 2.6 thick, a 14 square, 1 deep pocket on the
# sensor side with a 10.9 x 3.5 pad standing 0.6 in it
tid_back_plate = (24.2, 2.6)  # the puck's is 25: ours got pinched by the shaft walls and pushed up into the switch
tid_back_pocket = (14.0, 1.0)
tid_back_pad = (10.9, 3.5, 0.6, 0.21)  # across, front-to-back, height, offset toward the case
# The puck's pad held the sensor's switch down in the cap (no travel screwed tight,
# mushy loose; it clicks well with the plate off): lower its face this much. The test set
# tries tid_pad_drops; 0.2 won.
tid_pad_drop = 0.2
tid_pad_drops = (0.2, 0.4, 0.6, 0.8, 1.0)
tid_back_hole = 1.7  # M1.2 clearance
# Two legs hang from the cap through notches in the back plate to the pocket floor, M2 x 8
# self-tapping screws from the case bottom straight into their ends (sensor frame). A
# heat-set insert left the legs too thin a wall (0.8) to hold it; the pocket walls and the
# sensor's back leave no room for thicker legs.
tid_legs = [(-10.0, -5.125), (10.0, -5.125)]
tid_leg = 4.6
tid_leg_screw = 8.0  # length under the head, which sits in the case's counterbore
tid_leg_pilot = 1.8  # prints about 1.6, for the M2 to cut its thread in
tid_leg_gap = 0.2  # leg ends to the pocket floor, so the cap seats on the case first
tid_ribbon = (8.0, 2.4)  # slot (width, height) for the sensor cable into the case; its floor
# drops to the board pocket's (z 3.8) so the cable stays under the PCB
tid_slot_reach = 14.7  # how far the slot runs past the shaft's back into the case
tid_cable_turn = 12.2  # where along the slot the cable turns off for the board pocket
tid_cable_channel = 7.0  # floor channel from there to the board pocket (ribbon 3, plug 5)
tid_channel_skin = 0.6  # wall the channel leaves round a case standoff
pod_size = (30.0, 36.0)  # across and front-to-back round the pod centre; the case hides the back
pod_round = 3.5  # its front-right plan corner, like the case's outer corners (1.5 inside + the wall)
pod_tilt = 12.0  # the pod top: level with the case rim to a straight crease, then one flat face falling this much
tid_roof = 1.0  # the rim over the pocket behind the crease, where the sensor cable runs back

# Touch ID logic board (from the measurements page), in a pocket cut into the case floor
board_thick = 0.56 + 1.5 + 0.5  # PCB, tallest part on top, tallest part underneath
board_clearance = 0.4  # around the outline, per side
board_pocket = 3.2  # depth into the case floor
# Posts under its two 1.5 mm holes, an M1.2 x 4 self-tapping screw through each (pins snapped)
board_post = 3.0  # the ring round each hole is bare for 1.3 mm on the side that faces down
board_post_height = 1.5  # level with its tallest parts, which it lies upside down on
board_screw_pilot = 1.0
board_screw_depth = 4.5  # from the post top: 4 mm screw less the 0.56 board, plus spare
board_cable_bay = 11.2  # how far the pocket runs past the board's connector end: right up to
# the inner wall (11.6 away, less the clearance), so the folded Lightning ribbon lies flat
board_post_margin = 1.0  # floor the pocket leaves round a case standoff's foot
