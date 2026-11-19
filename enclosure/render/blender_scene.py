"""Product renders in Blender (Cycles), from the case glTF parts and the board glb.

  blender -b --python render/blender_scene.py -- hero <black|grey|blue|purple>
  blender -b --python render/blender_scene.py -- lineup
  blender -b --python render/blender_scene.py -- explode
  blender -b --python render/blender_scene.py -- carousel [frames]
  blender -b --python render/blender_scene.py -- explode_anim [frames]

Inputs: out/case_*.glb (case.py), out/pcb.glb (kicad-cli pcb export glb), out/screen.png.
Outputs: out/render/*.png, out/render/carousel/####.png
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
RENDER = OUT / "render"
MM = 0.001
T, L = 8.0 * MM, 101.9 * MM
AA_CY, DISPLAY_TOP = 75.83 * MM, 7.15 * MM
PCB_OFFSET = Vector((-0.1491, 0.1559, 0.005))      # board glb -> enclosure frame

VARIANTS = {   # anodized body colour, printed wheel colour
    "black": ((0.016, 0.017, 0.019), (0.004, 0.004, 0.005)),
    "grey": ((0.20, 0.205, 0.215), (0.12, 0.123, 0.128)),
    "blue": ((0.003, 0.012, 0.075), (0.005, 0.022, 0.13)),
    "purple": ((0.05, 0.008, 0.10), (0.055, 0.011, 0.12)),
}
PARTS = ["body", "plate", "engraving", "cap", "wheel", "button", "key", "glass",
         "battery", "gasket", "screw1", "screw2"]
DISPLAY = (26.6 * MM, 30.3 * MM, 0.741 * MM, 73.75 * MM)   # w, h, t, centre y (its glb imports rotated)


# --- scene ------------------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                break
        except TypeError:
            continue
    for d in prefs.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"
    sc.cycles.samples = 256
    sc.cycles.use_denoising = True
    # Debian's Blender has no OpenImageDenoise: use OptiX on the GPU
    sc.cycles.denoiser = "OPTIX" if prefs.compute_device_type == "OPTIX" else "OPENIMAGEDENOISE"
    print("cycles device", prefs.compute_device_type, [d.name for d in prefs.devices if d.use])
    sc.cycles.max_bounces = 10
    sc.cycles.transmission_bounces = 8
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.film_transparent = False
    world = bpy.data.worlds.new("world")
    sc.world = world
    world.use_nodes = True
    # dim light from the world, but a light grey background where the camera sees it
    nt = world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[0].default_value = (0.9, 0.9, 0.92, 1)
    bg.inputs[1].default_value = 0.06
    seen = nt.nodes.new("ShaderNodeBackground")
    seen.inputs[0].default_value = (0.30, 0.30, 0.31, 1)
    seen.inputs[1].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(seen.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs["Surface"])
    sc.render.use_persistent_data = True
    return sc


def mat(name, color, metallic=0.0, rough=0.5, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        p.inputs[k].default_value = v
    return m


def blasted(name, color):
    """Bead blasted anodized aluminium: metallic, fine noise in the roughness and bump."""
    m = mat(name, color, metallic=1.0, rough=0.38)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 9000.0
    tex.inputs["Detail"].default_value = 2.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = 0.32
    ramp.inputs["To Max"].default_value = 0.46
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], p.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.00002
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def screen_mat():
    m = mat("screen", (0.7, 0.7, 0.68), rough=0.35)
    nt = m.node_tree
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(str(OUT / "screen.png"))
    img.interpolation = "Closest"
    nt.links.new(img.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


def shared_materials():
    return {
        "chamfer": mat("diamond cut", (0.95, 0.95, 0.96), metallic=1.0, rough=0.06),
        "engraving": mat("laser marking", (0.86, 0.87, 0.88), metallic=0.6, rough=0.55),
        "black_plastic": mat("printed black", (0.006, 0.006, 0.007), rough=0.7, **{"Specular IOR Level": 0.3}),
        "glass": mat("cover glass", (1, 1, 1), rough=0.0, **{"Transmission Weight": 1.0, "IOR": 1.25}),  # AR coated
        "display": mat("display glass", (0.08, 0.085, 0.08), rough=0.15),
        "screen": screen_mat(),
        "screw": mat("black oxide", (0.05, 0.05, 0.055), metallic=1.0, rough=0.3),
        "battery": mat("pouch", (0.75, 0.75, 0.78), metallic=0.8, rough=0.35),
        "gasket": mat("gasket", (0.02, 0.02, 0.02), rough=0.8),
    }


def import_stl(path, collection):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=MM)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in o.users_collection:
            c.objects.unlink(o)
        collection.objects.link(o)
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
        o.select_set(False)
    return new


def import_glb(path, collection):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in o.users_collection:
            c.objects.unlink(o)
        collection.objects.link(o)
    return [o for o in new if o.type == "MESH"]


def split_chamfer(obj, chamfer, base):
    """Second material on the polished front chamfer (faces at ~45 deg near the front)."""
    obj.data.materials.clear()
    obj.data.materials.append(base)
    obj.data.materials.append(chamfer)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    for f in bm.faces:
        n = (mw.to_3x3() @ f.normal).normalized()
        c = mw @ f.calc_center_median()
        f.material_index = 1 if (0.45 < n.z < 0.9 and c.z > T - 0.5 * MM) else 0
    bm.to_mesh(obj.data)
    bm.free()


def build_device(name, variant, mats, explode=None):
    """One player as a collection under an empty (origin at the device centre)."""
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    body_c, wheel_c = VARIANTS[variant]
    alu = blasted(f"alu {variant}", body_c)
    wheel = mat(f"wheel {variant}", wheel_c, rough=0.55, **{"Specular IOR Level": 0.25})
    centre = Vector((0, L / 2, T / 2))
    parts = {}
    for p in PARTS:
        objs = import_stl(OUT / "mesh" / f"{p}.stl", col)
        parts[p] = objs
        for o in objs:
            o.data.materials.clear()
            m = {"body": alu, "plate": alu, "engraving": mats["engraving"], "cap": mats["black_plastic"],
                 "wheel": wheel, "button": wheel, "key": mats["black_plastic"], "glass": mats["glass"],
                 "display": mats["display"], "battery": mats["battery"], "gasket": mats["gasket"],
                 "screw1": mats["screw"], "screw2": mats["screw"]}[p]
            o.data.materials.append(m)
            if p == "body":
                split_chamfer(o, mats["chamfer"], alu)
    before = set(col.objects)
    import_glb(OUT / "pcb.glb", col)
    pcb_top = [o for o in col.objects if o not in before and o.parent is None]
    for o in pcb_top:
        o.location += PCB_OFFSET
    parts["pcb"] = pcb_top
    # display module (built here: its glb comes in rotated)
    w, h, t, cy = DISPLAY
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, cy, DISPLAY_TOP - t / 2))
    disp = bpy.context.object
    disp.scale = (w, h, t)
    for c in disp.users_collection:
        c.objects.unlink(disp)
    col.objects.link(disp)
    disp.data.materials.append(mats["display"])
    parts["display"] = [disp]
    # screen on the display, inside the glass
    bpy.ops.mesh.primitive_plane_add(size=23.04 * MM, location=(0, AA_CY, DISPLAY_TOP + 0.01 * MM))
    scr = bpy.context.object
    for c in scr.users_collection:
        c.objects.unlink(scr)
    col.objects.link(scr)
    scr.data.materials.append(mats["screen"])
    parts["screen"] = [scr]
    if explode:
        for p, off in explode.items():
            for o in parts.get(p, []):
                if o.parent is None:
                    o.location += Vector(off) * MM
    for objs in parts.values():
        for o in objs:
            if o.parent is None:
                o.parent = root
                o.matrix_parent_inverse = Matrix.Translation(-centre)
    LAST_PARTS.clear()
    LAST_PARTS.update(parts)
    return root


LAST_PARTS = {}


def studio(sc, size=1.0):
    """Seamless backdrop and three soft area lights, scaled around the origin."""
    bpy.ops.mesh.primitive_plane_add(size=4 * size, location=(0, 0, 0))
    floor = bpy.context.object
    bpy.ops.object.modifier_add(type="SOLIDIFY")
    floor.data.materials.append(mat("backdrop", (0.16, 0.16, 0.17), rough=0.75))
    # curve up behind
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, loc, energy, sz, color in (
            # low side lights: the top faces mirror the dark ceiling, the edges catch the light
            ("key", (0.40 * size, -0.20 * size, 0.14 * size), 8 * size ** 2, 0.30 * size, (1, 0.97, 0.93)),
            ("fill", (-0.40 * size, -0.25 * size, 0.10 * size), 2.5 * size ** 2, 0.45 * size, (0.93, 0.96, 1)),
            ("rim", (0.0, 0.45 * size, 0.16 * size), 6 * size ** 2, 0.25 * size, (1, 1, 1)),
            ("top", (0.0, -0.05 * size, 0.6 * size), 1.2 * size ** 2, 0.15 * size, (1, 1, 1))):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size, ld.color = energy, sz, color
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        d = Vector((0, 0, 0.01 * size)) - Vector(loc)
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return floor


def camera(sc, loc, target, lens=85, fstop=None, focus=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_start = 0.001
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus or (Vector(target) - Vector(loc)).length
    sc.camera = cam
    return cam


def pose(root, loc, rot_deg):
    root.location = loc
    root.rotation_euler = Euler([math.radians(a) for a in rot_deg])


def render(sc, path):
    RENDER.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("wrote", path)


# --- shots ---------------------------------------------------------------------------------
def hero(variant):
    sc = reset()
    mats = shared_materials()
    dev = build_device(f"mp3 {variant}", variant, mats)
    # lying on the floor, front up, slightly turned; a second one behind shows the back
    pose(dev, (0.0, 0.0, T / 2), (0, 0, 28))
    back = build_device(f"mp3 {variant} back", variant, mats)
    pose(back, (0.075, 0.055, T / 2), (0, 180, -14))
    studio(sc, 0.6)
    camera(sc, (0.10, -0.24, 0.20), (0.03, 0.01, 0.0), lens=70, fstop=6.0)
    render(sc, RENDER / f"hero_{variant}.png")


def lineup():
    sc = reset()
    mats = shared_materials()
    for i, v in enumerate(VARIANTS):
        d = build_device(f"mp3 {v}", v, mats)
        pose(d, (-0.075 + i * 0.05, 0.0, T / 2), (0, 0, 0))
    studio(sc, 0.8)
    camera(sc, (0.0, -0.30, 0.26), (0.0, 0.0, 0.0), lens=60, fstop=4.0)
    render(sc, RENDER / "lineup.png")


EXPLODE = {   # mm, enclosure frame (z = thickness, front +z): back parts down, front parts up
    "screw1": (0, 0, -58), "screw2": (0, 0, -58), "plate": (0, 0, -46), "gasket": (0, 0, -38),
    "battery": (0, 0, -30), "pcb": (0, 0, -18), "display": (0, 0, -9), "screen": (0, 0, -9),
    "glass": (0, 0, 16), "wheel": (0, 0, 12), "button": (0, 0, 20), "key": (16, 0, 0),
    "cap": (0, 24, 0),
}


EXPLODE_ORDER = ["screw1", "screw2", "plate", "gasket", "battery", "pcb", "display", "screen",
                 "key", "cap", "glass", "button", "wheel"]


def explode_anim(frames=210):
    """Assembled -> exploded (staggered, eased) -> hold -> back together, camera orbiting."""
    sc = reset()
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    # dark studio: the floor fades into black instead of a grey horizon band
    sc.world.node_tree.nodes["Background.001"].inputs[0].default_value = (0.012, 0.012, 0.014, 1)
    mats = shared_materials()
    d = build_device("mp3 exploded", "blue", mats)
    # standing on its bottom end, front toward the camera; the stack opens front/back
    pose(d, (0, 0, L / 2 + 0.0005), (90, 0, -12))
    studio(sc, 0.8)
    target = Vector((0.0, 0.0, 0.056))
    pivot = bpy.data.objects.new("orbit", None)
    sc.collection.objects.link(pivot)
    pivot.location = target
    cam = camera(sc, (0.25, -0.31, 0.12), target, lens=50, fstop=11.0)
    bpy.context.view_layer.update()
    cam.parent = pivot
    cam.matrix_parent_inverse = pivot.matrix_world.inverted()
    out_start, out_len, stagger = 20, 45, 3
    hold_end = 130
    for i, p in enumerate(EXPLODE_ORDER):
        off = Vector(EXPLODE[p]) * MM
        for o in LAST_PARTS.get(p, []):
            base = o.location.copy()
            f0 = out_start + i * stagger
            f1 = hold_end + (len(EXPLODE_ORDER) - 1 - i) * stagger   # reassemble in reverse order
            for f, loc in ((f0, base), (f0 + out_len, base + off), (f1, base + off), (f1 + out_len, base)):
                o.location = loc
                o.keyframe_insert("location", frame=f)
            for fc in o.animation_data.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = "BEZIER"
                    k.easing = "EASE_IN_OUT"
    pivot.rotation_euler = (0, 0, math.radians(-12))
    pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, math.radians(18))
    pivot.keyframe_insert("rotation_euler", frame=frames)
    sc.frame_start, sc.frame_end = 1, frames
    (RENDER / "explode_anim").mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(RENDER / "explode_anim" / "####")
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)


def explode():
    sc = reset()
    mats = shared_materials()
    d = build_device("mp3 exploded", "blue", mats, explode=EXPLODE)
    pose(d, (0, 0, 0.066), (0, 0, -32))    # flat, front up, the stack spread vertically
    studio(sc, 0.8)
    camera(sc, (0.20, -0.27, 0.21), (0.0, 0.004, 0.058), lens=55, fstop=11.0)
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1200
    render(sc, RENDER / "explode.png")


def carousel(frames=120):
    sc = reset()
    sc.cycles.samples = 40
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    mats = shared_materials()
    turntable = bpy.data.objects.new("turntable", None)
    sc.collection.objects.link(turntable)
    r = 0.06
    PLINTH = 0.006
    for i, v in enumerate(VARIANTS):
        d = build_device(f"mp3 {v}", v, mats)
        a = i * math.pi / 2
        pose(d, (r * math.sin(a), -r * math.cos(a), PLINTH + L / 2 + 0.0002), (90, 0, math.degrees(a)))
        d.parent = turntable
    bpy.ops.mesh.primitive_cylinder_add(radius=0.105, depth=PLINTH, location=(0, 0, PLINTH / 2), vertices=128)
    disc = bpy.context.object
    disc.data.materials.append(mat("plinth", (0.85, 0.85, 0.86), rough=0.3))
    studio(sc, 0.8)
    camera(sc, (0.0, -0.50, 0.16), (0.0, 0.0, 0.055), lens=50, fstop=8.0, focus=0.45)
    sc.frame_start, sc.frame_end = 1, frames
    turntable.rotation_euler = (0, 0, 0)
    turntable.keyframe_insert("rotation_euler", frame=1)
    turntable.rotation_euler = (0, 0, 2 * math.pi)
    turntable.keyframe_insert("rotation_euler", frame=frames + 1)
    for fc in turntable.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    (RENDER / "carousel").mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(RENDER / "carousel" / "####")
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["hero", "grey"]
    if args[0] == "hero":
        hero(args[1] if len(args) > 1 else "grey")
    elif args[0] == "lineup":
        lineup()
    elif args[0] == "explode":
        explode()
    elif args[0] == "explode_anim":
        explode_anim(int(args[1]) if len(args) > 1 else 210)
    elif args[0] == "carousel":
        carousel(int(args[1]) if len(args) > 1 else 120)
