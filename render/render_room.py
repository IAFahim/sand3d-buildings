import bpy, sys, functools
import mathutils

glb, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "exterior"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bs = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
center = functools.reduce(lambda a, b: a + b, bs) / len(bs)
radius = max((center - b).length for b in bs)

cam_data = bpy.data.cameras.new("cam"); cam_data.lens = 24 if mode == "interior" else 55
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)

if mode == "interior":
    # inside the back of the room, looking at the front wall (door + windows)
    cam.location = center + mathutils.Vector((-1.15, 0.0, 0.35))
    aim = center + mathutils.Vector((1.68, 0.0, -0.15))
    sun_dir = mathutils.Vector((2.5, 1.2, 1.6))  # sun outside the front wall
else:
    d = mathutils.Vector((2.1, -1.2, 0.55)).normalized()
    cam.location = center + d * radius * 2.35
    aim = center
    sun_dir = mathutils.Vector((2.5, -0.4, 1.8))  # sun on the front-left, lights the +X face

cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

light_data = bpy.data.lights.new("key", 'SUN'); light_data.energy = 4
light_data.angle = 0.526  # softer shadows
light = bpy.data.objects.new("key", light_data)
light.rotation_euler = (-sun_dir).to_track_quat('-Z', 'Y').to_euler()
bpy.context.collection.objects.link(light)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
try:
    scene.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.get_devices()
    for dt in prefs.devices:
        dt.use = dt.type in ('OPTIX', 'CUDA')
except Exception as e:
    print("GPU setup failed, CPU:", e)
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1100
scene.render.resolution_y = 850
scene.world = bpy.data.worlds.new("w"); scene.world.use_nodes = True
bg = scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.55, 0.7, 0.95, 1.0)
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered", out)
