# Keyball61 case CAD

[build123d](https://github.com/gumyr/build123d) source for the printed parts in
[`../3d-prints`](../3d-prints). The bottom cases and switch plates were redrawn from the
original Fusion 360 prints for the bought Keyball61 Bluetooth PCB. The lids, Touch ID pod
and TPU palm rest were designed here.

## Use

Needs [uv](https://docs.astral.sh/uv/).

```bash
uv run switch_plate.py
uv run case.py
uv run lid.py        # also writes *_lid_test_ring: print one first to check the fit
uv run palm_rest.py  # TPU lattice palm rest; one part fits both halves
```

Each script writes `out/<part>.step` in design orientation (it imports into Fusion), plus
`.stl` and `.3mf` posed for printing: plates switch-side down, cases bottom down, lids
top down. `touchid.py` is called by `case.py` and `lid.py`; `foam_template.py` writes a
cutting template for the foam under the Touch ID board.

## Files

| File | Contents |
| --- | --- |
| `params.py` | Dimensions and clearances |
| `layout_left.py`, `layout_right.py` | Per half: keys, plate outline, insert positions, case outline, palm tray, controller pocket, port, feet |
| `switch_plate.py` | MX switch plate with heat-set insert bosses |
| `case.py` | Bottom case with the palm tray and screw counterbores |
| `lid.py` | Snap-on dust lids, drawn from the case outline with a 0.3 mm gap |
| `touchid.py` | Left case Touch ID pod, cap, back plate and logic-board pocket |
| `palm_rest.py` | TPU Voronoi-lattice palm rest |
| `profiles/` | Bambu Studio presets for Overture TPU 95A on a P2S (0.4 and 0.6 nozzle) |

Insert positions (`INSERTS` in the layout files) match the bought keyboard's PCB: 9 on the
left, 8 on the right.
