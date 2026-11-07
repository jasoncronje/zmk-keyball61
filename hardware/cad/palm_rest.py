"""TPU foam-lattice palm rest, a drop-in for the wooden rest on the case's palm tray.

Run `uv run palm_rest.py` to write out/palm_rest.{stl,3mf} (a mesh: no STEP). One part
serves both halves; print two. It prints the way it sits, bottom on the bed.

The block is the wooden rest's: palm_rest_size in plan, palm_rest_back tall against the
case front, its top curving down to palm_rest_front at the front edge. It is filled with
a 3D Voronoi web of round struts on a solid floor. Seeds near each outside face are
mirrored across it, so the Voronoi faces between them lie on that face: the web closes
into a net over the top, sides, front and back instead of ending in cut stubs. The
cells are drawn palm_rest_stretch taller than wide, so struts lean steeply and fewer of
them print as flat bridges.
"""

import itertools

import manifold3d as mf
import numpy as np
import trimesh
from build123d import Spline
from scipy.spatial import Voronoi

import layout_left as left
import layout_right as right
from case import outlines
from params import (
    case_wall,
    palm_rest_back,
    palm_rest_cell,
    palm_rest_floor,
    palm_rest_front,
    palm_rest_seed,
    palm_rest_size,
    palm_rest_slope,
    palm_rest_stretch,
    palm_rest_strut,
    tray_floor,
)
from switch_plate import OUT

# Frame: x across, centred; y = 0 at the back face (against the case front), the front
# edge at y = -depth; z = 0 at the bottom.

R = palm_rest_strut / 2


def top_curve(n: int = 400) -> np.ndarray:
    """The top's side profile as (y, z) samples, back to front."""
    d = palm_rest_size[1]
    top = Spline((0, palm_rest_back), (-d, palm_rest_front), tangents=[(-1, 0), (-1, -palm_rest_slope)])
    return np.array([(p.X, p.Y) for p in (top @ (i / (n - 1)) for i in range(n))])


class Skeleton:
    """The volume the strut centre lines fill: the block shrunk by a strut radius, so
    the struts' outsides land on the block's faces. Worked in a space squashed by
    palm_rest_stretch in z, where the cells are round."""

    def __init__(self):
        w, d = palm_rest_size
        self.x = w / 2 - R
        self.y0, self.y1 = -d + R, -R
        self.z0 = palm_rest_floor / 2 / palm_rest_stretch  # bottom net sinks into the floor
        curve = top_curve()
        self.curve = np.column_stack([curve[:, 0], (curve[:, 1] - R) / palm_rest_stretch])

    def top(self, y):
        return np.interp(y, self.curve[::-1, 0], self.curve[::-1, 1])

    def inside(self, p, tol=0.0):
        x, y, z = p[..., 0], p[..., 1], p[..., 2]
        return ((np.abs(x) <= self.x + tol) & (y >= self.y0 - tol) & (y <= self.y1 + tol)
                & (z >= self.z0 - tol) & (z <= self.top(y) + tol))

    def mirrors(self, p, reach):
        """p reflected across every face within reach of it, and across each pair and
        triple of those faces (corners)."""
        x, y, z = p
        flips = []
        if self.x - x < reach:
            flips.append(lambda q: (2 * self.x - q[0], q[1], q[2]))
        if x + self.x < reach:
            flips.append(lambda q: (-2 * self.x - q[0], q[1], q[2]))
        if self.y1 - y < reach:
            flips.append(lambda q: (q[0], 2 * self.y1 - q[1], q[2]))
        if y - self.y0 < reach:
            flips.append(lambda q: (q[0], 2 * self.y0 - q[1], q[2]))
        if z - self.z0 < reach:
            flips.append(lambda q: (q[0], q[1], 2 * self.z0 - q[2]))
        if self.top(y) - z < reach:
            # across the curve's nearest point: locally the tangent line
            i = np.argmin(np.hypot(self.curve[:, 0] - y, self.curve[:, 1] - z))
            cy, cz = self.curve[i]
            flips.append(lambda q, cy=cy, cz=cz: (q[0], 2 * cy - q[1], 2 * cz - q[2]))
        out = []
        for k in range(1, len(flips) + 1):
            for combo in itertools.combinations(flips, k):
                q = p
                for f in combo:
                    q = f(q)
                out.append(q)
        return out


def seeds(sk: Skeleton, rng) -> np.ndarray:
    """Blue-noise seeds filling the skeleton (dart throwing), no two closer than
    0.85 cell."""
    lo = np.array([-sk.x, sk.y0, sk.z0])
    hi = np.array([sk.x, sk.y1, sk.curve[:, 1].max()])
    gap = 0.85 * palm_rest_cell
    pts = np.empty((0, 3))
    for _ in range(40000):
        p = lo + rng.random(3) * (hi - lo)
        if not sk.inside(p):
            continue
        if len(pts) and np.min(np.linalg.norm(pts - p, axis=1)) < gap:
            continue
        pts = np.vstack([pts, p])
    return pts


def web(sk: Skeleton, rng):
    """Strut segments (pairs of points, real space) of the Voronoi web."""
    inner = seeds(sk, rng)
    mirrored = [q for p in inner for q in sk.mirrors(tuple(p), 1.5 * palm_rest_cell)]
    vor = Voronoi(np.vstack([inner, mirrored]))
    v = vor.vertices
    keep = sk.inside(v, tol=0.02 * palm_rest_cell)

    # merge vertices closer than a strut: Voronoi throws up tiny edges near the faces
    merge = palm_rest_strut
    index = -np.ones(len(v), dtype=int)
    centres = []
    for i in np.flatnonzero(keep):
        for j, c in enumerate(centres):
            if np.linalg.norm(v[i] - c) < merge:
                index[i] = j
                break
        else:
            index[i] = len(centres)
            centres.append(v[i])
    centres = np.array(centres)

    edges = set()
    for ridge in vor.ridge_vertices:
        if -1 in ridge:
            continue
        for a, b in zip(ridge, ridge[1:] + ridge[:1]):
            if keep[a] and keep[b] and index[a] != index[b]:
                edges.add(tuple(sorted((index[a], index[b]))))
    real = centres * np.array([1, 1, palm_rest_stretch])
    # snap the centre lines back onto the skeleton (merging can pull a face net off its face)
    real[:, 0] = np.clip(real[:, 0], -sk.x, sk.x)
    real[:, 1] = np.clip(real[:, 1], sk.y0, sk.y1)
    real[:, 2] = np.minimum(real[:, 2], sk.top(real[:, 1]) * palm_rest_stretch)
    return real, sorted(edges)


def palm_rest() -> trimesh.Trimesh:
    sk = Skeleton()
    nodes, edges = web(sk, np.random.default_rng(palm_rest_seed))
    segments = 16
    ball = mf.Manifold.sphere(R, segments)
    struts = [mf.Manifold.batch_hull([ball.translate(tuple(nodes[a])), ball.translate(tuple(nodes[b]))])
              for a, b in edges]
    w, d = palm_rest_size
    floor = mf.Manifold.cube((w, d, palm_rest_floor)).translate((-w / 2, -d, 0))
    body = mf.Manifold.batch_boolean(struts + [floor], mf.OpType.Add)
    # nothing below the bed (struts round the bottom net reach under the floor)
    body = body.trim_by_plane((0, 0, 1), 0.0)
    mesh = body.to_mesh()
    part = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts, process=True)
    part.metadata["struts"] = len(edges)
    part.metadata["nodes"] = len(nodes)
    # struts flatter than 25 degrees print as bridges (those in the floor don't count)
    flat = [abs(nodes[b][2] - nodes[a][2]) / np.linalg.norm(nodes[b] - nodes[a]) < np.sin(np.radians(25))
            and max(nodes[a][2], nodes[b][2]) > palm_rest_floor for a, b in edges]
    lengths = [np.linalg.norm(nodes[b] - nodes[a]) for a, b in edges]
    part.metadata["flat"] = [l for l, f in zip(lengths, flat) if f]
    return part


def tray_pos(layout):
    """Where the rest sits on a case's tray: centred between its side walls, back face
    on the case front, bottom on the tray floor."""
    tray = outlines(layout)[2].bounding_box()
    inside = tray.size.X - 2 * case_wall
    w, d = palm_rest_size
    assert w < inside and d < layout.CASE_FRONT - layout.TRAY_FRONT, "palm rest doesn't fit the tray"
    return (tray.center().X, layout.CASE_FRONT, tray_floor)


def export(part: trimesh.Trimesh, name: str = "palm_rest") -> None:
    OUT.mkdir(exist_ok=True)
    part.export(OUT / f"{name}.stl")
    part.export(OUT / f"{name}.3mf")


TRAYS = {"left": left, "right": right}

if __name__ == "__main__":
    part = palm_rest()
    tpu_density = 1.21  # g/cm^3, TPU 95A
    flat = part.metadata["flat"]
    print(f"palm_rest: {part.metadata['struts']} struts, {part.metadata['nodes']} nodes, "
          f"volume {part.volume:.0f} mm^3 (~{part.volume / 1000 * tpu_density:.0f} g TPU), "
          f"bbox {np.round(part.extents, 2)}, watertight {part.is_watertight}, {len(part.faces)} triangles")
    print(f"  {len(flat)} struts flatter than 25 deg, longest {max(flat, default=0):.1f} mm")
    for side, layout in TRAYS.items():
        print(f"  {side} tray position {tuple(round(v, 3) for v in tray_pos(layout))}")
    export(part)
