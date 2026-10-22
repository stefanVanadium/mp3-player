"""README image: chosen variant, front and back side by side.

Run: .venv/bin/python render/hero.py out  ->  out/hero_B.png
"""
import sys
from pathlib import Path

import matplotlib.image
import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import concept  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
v = next(x for x in concept.VARIANTS if x.name == "B")
_, parts = concept.build(v)
SHOW = ("body", "cap", "wheel", "button", "key", "LS013")  # outside only

p = pv.Plotter(off_screen=True, window_size=(1800, 1300))
p.enable_anti_aliasing("ssaa")
p.set_background("white")
p.remove_all_lights()
p.add_light(pv.Light(position=(-150, 200, 300), intensity=0.85, light_type="scene light"))
p.add_light(pv.Light(position=(250, -100, 150), intensity=0.35, light_type="scene light"))
p.add_light(pv.Light(position=(0, 60, -300), intensity=0.3, light_type="scene light"))


def turn(P, deg):
    """Rotate about the device's own long axis (through its centre)."""
    a = np.radians(deg)
    x, z = P[:, 0], P[:, 2] - v.thickness / 2
    return np.column_stack([x * np.cos(a) + z * np.sin(a), P[:, 1],
                            -x * np.sin(a) + z * np.cos(a) + v.thickness / 2])


for flip, dx, deg in ((False, -27.0, -22.0), (True, 27.0, 22.0)):
    for shape, label, color in parts:
        if not any(s in label for s in SHOW):
            continue
        verts, tris = shape.tessellate(0.01, 0.1)
        P = np.array([[q.X, q.Y, q.Z] for q in verts])
        T = np.array(tris)
        if flip:  # turn the copy around its long axis to show the back
            P[:, 0] *= -1
            P[:, 2] = v.thickness - P[:, 2]
            T = T[:, ::-1]
        P = turn(P, deg)
        P[:, 0] += dx
        mesh = pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel())
        mesh = mesh.compute_normals(split_vertices=True, feature_angle=35)
        glossy = "LS013" in label
        p.add_mesh(mesh, color=tuple(color)[:3], smooth_shading=True, pbr=False,
                   specular=0.9 if glossy else 0.45, specular_power=40 if glossy else 18,
                   ambient=0.18, diffuse=0.8)

c = np.array([0, v.length / 2 + 3, v.thickness / 2])
p.camera.position = tuple(c + np.array([0, -60, 330]))
p.camera.focal_point = tuple(c)
p.camera.up = (0, 1, 0)
p.camera.view_angle = 30
img = p.screenshot(transparent_background=True, return_img=True)
alpha = img[:, :, 3] > 0
rows, cols = np.where(alpha.any(1))[0], np.where(alpha.any(0))[0]
m = 40  # crop to the models plus a margin
img = img[max(rows[0] - m, 0):rows[-1] + m, max(cols[0] - m, 0):cols[-1] + m]
matplotlib.image.imsave(out / f"hero_{v.name}.png", img)
print("wrote", out / f"hero_{v.name}.png")
