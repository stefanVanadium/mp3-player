import sys, numpy as np, pyvista as pv
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import concept
out = sys.argv[1]
HIDE = ("body", "cap", "wheel", "button", "key")
# camera direction (from object centre), view-up
views = [("front", (0.9, -1.2, 1.6), (0, 1, 0), False),
         ("back", (-0.9, -1.4, -1.5), (0, 1, 0), False),
         ("bottom end", (0.35, -2.0, -0.45), (0, 0, 1), False),
         ("side", (2.0, 0.0, -0.0001), (0, 1, 0), False),
         ("inside, from back", (-0.9, -1.2, -1.5), (0, 1, 0), True),
         ("inside, front shell hidden", (0.9, -1.2, 1.6), (0, 1, 0), True)]
for v in concept.VARIANTS:
    _, parts = concept.build(v)
    meshes = []
    for shape, label, color in parts:
        verts, tris = shape.tessellate(0.02, 0.15)
        P = np.array([[p.X, p.Y, p.Z] for p in verts]); T = np.array(tris)
        faces = np.hstack([np.full((len(T), 1), 3), T]).ravel()
        meshes.append((label, pv.PolyData(P, faces), tuple(color)[:3]))
    p = pv.Plotter(off_screen=True, shape=(2, 3), window_size=(1800, 1300), border=False)
    c = np.array([0, v.length / 2, v.thickness / 2])
    for i, (name, d, up, hide) in enumerate(views):
        p.subplot(i // 3, i % 3)
        for label, m, col in meshes:
            if hide and any(h in label for h in HIDE): continue
            p.add_mesh(m, color=col, smooth_shading=False, specular=0.3, metallic=0.0)
        d = np.array(d) / np.linalg.norm(d)
        p.camera.position = tuple(c + d * 260); p.camera.focal_point = tuple(c); p.camera.up = up
        p.camera.view_angle = 30 if name != "bottom end" else 14
        p.add_text(name, font_size=11, color="black")
        p.set_background("white")
    p.screenshot(f"{out}/render_{v.name}.png"); p.close()
    print("ok", v.name)
