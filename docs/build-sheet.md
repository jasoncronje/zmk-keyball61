# Keyball61 build sheet

These mods are intended for the **Keyball61 Bluetooth keyboards sold by generic sellers on AliExpress**. This guide covers custom cases, MX switch plates, snap-on lids, TPU palm rests, a Touch ID mod, and hardware upgrades for those keyboards.

Hardware can vary between sellers and revisions. If you find any fitment or compatibility issues, please send a PR with the details and any fixes so other builders can benefit.

## Print files

Download the 3MF files and open them in your slicer. The parts are modelled in code: the [build123d source](../hardware/cad) can regenerate or modify any of them.

| Part | Qty | File |
| --- | --- | --- |
| Left case | 1 | [left_case.3mf](../hardware/3d-prints/cases/left_case.3mf) |
| Right case | 1 | [right_case.3mf](../hardware/3d-prints/cases/right_case.3mf) |
| Left MX switch plate | 1 | [left_switch_plate.3mf](../hardware/3d-prints/switch-plates/left_switch_plate.3mf) |
| Right MX switch plate | 1 | [right_switch_plate.3mf](../hardware/3d-prints/switch-plates/right_switch_plate.3mf) |
| Left lid | 1 | [left_lid.3mf](../hardware/3d-prints/lids/left_lid.3mf) (fit test: [left_lid_test_ring.3mf](../hardware/3d-prints/lids/left_lid_test_ring.3mf)) |
| Right lid | 1 | [right_lid.3mf](../hardware/3d-prints/lids/right_lid.3mf) (fit test: [right_lid_test_ring.3mf](../hardware/3d-prints/lids/right_lid_test_ring.3mf)) |
| Palm rest (TPU) | 2 | [palm_rest_tpu.3mf](../hardware/3d-prints/palm-rests/palm_rest_tpu.3mf) |
| Touch ID cap | 1 | [left_touchid_cap.3mf](../hardware/3d-prints/touch-id/left_touchid_cap.3mf) |
| Touch ID back plate | 1 | [left_touchid_back_plate.3mf](../hardware/3d-prints/touch-id/left_touchid_back_plate.3mf) |
| Trackball cup and sensor cover | 1 | Coming soon |

**MX switches only, including the thumbs.** Each plate combines the main and thumb sections into one piece. Bottom-access screws thread into heat-set inserts, so the PCB, plate, and switches can be removed together for servicing.

The left case has a pod at the thumb corner for the [Touch ID mod](#touch-id-mod). Both cases have a palm tray at the front.

The lids snap over the cases to protect the keys during storage and travel: bumps inside the skirt click into dimples in the case walls. The right lid is open over the trackball. Print a test ring first to check the snap fit before printing a full lid. Check clearance if using a different keycap profile.

### Printing

- The cases, plates and Touch ID parts were printed in **PLA**, the lids in clear **PETG**. Either material works for the lids. Other materials can be used with suitable settings and clearance adjustments. Avoid leaving PLA parts in a hot car.
- The palm rests are printed in **Overture TPU 95A** with a 0.6 mm nozzle; the 3MF carries the Bambu Studio settings. Expect "floating regions" warnings from tiny mesh slivers; they're safe to ignore. Matching [Bambu Studio presets](../hardware/cad/profiles) are included.
- Print at **100% scale, in millimetres**. Select your own printer and material settings; some 3MF files include a Bambu Studio profile.
- Check orientation and supports before slicing. Keep switch openings, insert pockets, and mating surfaces clean.
- Test-fit a switch, the PCB, and the battery before final assembly.

## Parts

Quantities cover both halves. Switches, keycaps, trackball, and palm rests can be substituted to suit your preferences.

| Part | Quantity | Specification / link |
| --- | --- | --- |
| Switches | 61 | [DUROCK Silent Shrimp](https://www.amazon.com/dp/B0B219QP6T): silent tactile, 67 g, 5-pin MX; 70-pack |
| Keycaps | 1 set | [YMDK XDA 96](https://www.amazon.com/dp/B0F7RHW9Y1): blank PBT, MX stems |
| Trackball | 1 | [Perixx PERIPRO-303](https://www.amazon.com/dp/B0D4F4HMXD): 34 mm; linked variant is glossy white |
| Palm rests | 1 pair | Print the TPU rests above, or use [YMDK mini walnut rests](https://www.amazon.com/dp/B0BNV8BVBG), or make your own below |
| Batteries | 2 | [Liter 3.7 V, 1,500 mAh LiPo](https://www.amazon.com/dp/B09GFQY6ZR): 5.2 × 41 × 52 mm; connector adaptation required for this build |
| Power switches | 2 | [Nidec CUS-12TB](https://www.digikey.com/en/products/detail/nidec-components/CUS-12TB/1124222): surface-mount SPDT, on-on |
| Heat-set inserts | 17 | M2, 3 mm long; included in this [Kadrick assortment](https://www.amazon.com/dp/B0D5V3TZLB) |
| Screws | 17 | M2 socket-head cap screws; [assortment with 4–20 mm lengths](https://www.amazon.com/dp/B0D3X4LJD2) |

### Mounting hardware

Use **M2 inserts, 3 mm long, with a 3 mm top knurl diameter and 2.7 mm lower shaft diameter**. Match the outside dimensions as well as the thread size.

The cases accommodate socket heads approximately **3.78 mm wide × 2 mm high**. **Screw length is not yet specified:** check the assembled depth and choose a length that engages the insert without bottoming out or contacting the PCB or battery.

### Palm rests

The printed TPU rest is a 3D lattice the size of the walnut rest: 100 × 79 mm, 20 mm tall at the back, curving down to 8 mm at the front. One part fits either tray; print two. Each takes about 75 g of TPU and 8.5 hours on a 0.6 mm nozzle.

The trays have two slots each for 12.6 mm wide, 1 mm thin VHB tape, which holds a wooden rest down without lifting it.

For DIY wooden rests, use two blocks with an overall size of **100 × 79 × 20 mm each** (3.94 × 3.11 × 0.79 inches), matching the [mini rests](https://www.amazon.com/dp/B0BNV8BVBG). Round and sand the edges, finish the surface, and add non-slip feet. Shape the top and adjust the height to suit your hands; these dimensions describe the overall size, not the commercial rest's exact curved profile.

## Assembly

1. Disconnect USB and unplug both batteries. Complete any battery or power-switch upgrades below before fitting the boards into the cases.
2. Heat-set the inserts into the underside plate pockets. Keep them straight and let the plastic cool before installing screws.
3. Fit the MX switches through the plates into the PCBs, supporting the hot-swap sockets as you press.
4. Place the assemblies in the cases with wires clear of screw paths. Fasten from underneath without overtightening.
5. Fit the keycaps and trackball. Check every key, trackball movement, power switching, charging, and wireless connection.
6. Check that the lids snap on without pressing on keys, displays, or the trackball. Turn both halves off before packing.

For servicing, remove the bottom screws and lift out the PCB, plate, and switches together, taking care with attached wires.

### Battery upgrade

The linked batteries use a JST PH 2.0 mm connector. This build reuses the original keyboard battery connectors, spliced onto the new battery leads.

If adapting the leads, work on **one wire at a time**; never cut both live battery wires together. Verify connector polarity with a meter, insulate each splice with heat-shrink, and provide strain relief. Solder only the leads, never the pouch cell. The battery must fit without being compressed when the case closes.

### Touch ID mod

The left case carries the Touch ID sensor from an Apple Magic Keyboard with Touch ID. The sensor sits flush in the sloping cap of the pod at the thumb corner. Its logic board lies upside down in a pocket in the case floor, and the sensor cable runs to it through a slot in the case's front wall.

- **Sensor:** the sensor and its c-plate clamp up against the cap's skin with the printed back plate and six M1.2 screws.
- **Cap:** two legs reach down into the case and are fastened from the bottom with M2 × 8 mm self-tapping screws.
- **Logic board:** held on two posts with short M1.2 screws. Cut foam to fit under it; `foam_template.py` in the [CAD source](../hardware/cad) writes a cutting template.

A full wiring and power guide for this mod is not written yet.

### Power-switch upgrade

The CUS-12TB is a soldered replacement for the switches on this build. Check the footprint and actuator orientation against your PCB revision before ordering. With USB and batteries disconnected, desolder the old switch, clean the pads, and solder the replacement. Check for bridges and verify continuity before reconnecting power.
