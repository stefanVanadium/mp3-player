import sys, numpy as np, pyvista as pv
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import concept
out = sys.argv[1]
p = pv.Plotter(off_screen=True, shape=(2, 2), window_size=(1800, 1000), border=False)
for i, v in enumerate(concept.VARIANTS):
    _, parts = concept.build(v)
    p.subplot(i // 2, i % 2); p.set_background("white")
    for shape, label, color in parts:
        verts, tris = shape.tessellate(0.02, 0.15)
        P = np.array([[q.X, q.Y, q.Z] for q in verts]); T = np.array(tris)
        p.add_mesh(pv.PolyData(P, np.hstack([np.full((len(T), 1), 3), T]).ravel()), color=tuple(color)[:3], specular=0.3)
    c = np.array([0, 0, v.thickness / 2])
    p.camera.position = (0, -200, v.thickness / 2); p.camera.focal_point = (0, 0, v.thickness / 2); p.camera.up = (0, 0, 1); p.enable_parallel_projection(); p.camera.parallel_scale = 13
    p.add_text(f"{v.name}: bottom end, orthographic", font_size=12, color="black")
p.screenshot(f"{out}/ends_ortho.png")
