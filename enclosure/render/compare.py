import sys, numpy as np, pyvista as pv
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import concept
out = sys.argv[1]
p = pv.Plotter(off_screen=True, window_size=(2400, 1000))
p.set_background("white")
dx = 0
for v in concept.VARIANTS:
    _, parts = concept.build(v)
    for flip in (False, True):
        for shape, label, color in parts[:6]:
            verts, tris = shape.tessellate(0.02, 0.15)
            P = np.array([[q.X, q.Y, q.Z] for q in verts])
            if flip: P[:, 0] *= -1; P[:, 2] = v.thickness - P[:, 2]; T = np.array(tris)[:, ::-1]
            else: T = np.array(tris)
            P[:, 0] += dx
            p.add_mesh(pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel()), color=tuple(color)[:3], specular=0.3)
        p.add_point_labels([(dx, -8, 0)], [f"{v.name} {'back' if flip else 'front'}"], font_size=20, shape=None, show_points=False, text_color="black")
        dx += 52
    p.add_point_labels([(dx - 78, 112, 0)], [f"{v.name}: {v.width:g} x {v.length:g} x {v.thickness:g} mm"], font_size=22, shape=None, show_points=False, text_color="black")
    dx += 14
p.camera.position = (dx / 2 - 40, 30, 420); p.camera.focal_point = (dx / 2 - 40, 50, 0); p.camera.up = (0, 1, 0); p.camera.view_angle = 30; p.camera.zoom(1.0)
p.screenshot(f"{out}/compare.png")
