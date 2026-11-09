import bpy, sys, functools
import mathutils

glb, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "exterior"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']

# --- procedural brick on the walls part ---
walls_obj = next(o for o in meshes if o.name.startswith("walls"))
nt = walls_obj.data.materials[0].node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
brick, tc, mapping, bump = (nt.nodes.new(t) for t in
    ('ShaderNodeTexBrick', 'ShaderNodeTexCoord', 'ShaderNodeMapping', 'ShaderNodeBump'))
mapping.inputs['Scale'].default_value = (2.8, 2.8, 2.8)
brick.inputs['Color1'].default_value = (0.60, 0.25, 0.16, 1.0)
brick.inputs['Color2'].default_value = (0.50, 0.20, 0.13, 1.0)
brick.inputs['Mortar'].default_value = (0.85, 0.81, 0.73, 1.0)
brick.inputs['Mortar Size'].default_value = 0.025
brick.inputs['Bias'].default_value = 0.15
bump.inputs['Strength'].default_value = 0.25
nt.links.new(tc.outputs['Generated'], mapping.inputs['Vector'])
nt.links.new(mapping.outputs['Vector'], brick.inputs['Vector'])
nt.links.new(brick.outputs['Fac'], bump.inputs['Height'])
nt.links.new(brick.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value = 0.95

# --- camera ---
bs = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
center = functools.reduce(lambda a, b: a + b, bs) / len(bs)
radius = max((center - b).length for b in bs)

cam_data = bpy.data.cameras.new("cam"); cam_data.lens = 20 if mode == "interior" else 52
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)

if mode == "interior":
    cam.location = mathutils.Vector((0.75, 1.05, 1.55))          # inside, near the door
    aim = mathutils.Vector((-0.1, -1.4, 1.5))                    # the -Y louvered window
    sun_dir = mathutils.Vector((0.4, -2.2, 1.9))                 # tropical sun beyond that window
else:
    d = mathutils.Vector((1.7, -1.25, 0.42)).normalized()
    cam.location = center + d * radius * 2.5
    aim = center
    sun_dir = mathutils.Vector((1.1, -2.2, 1.7))
cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

light_data = bpy.data.lights.new("key", 'SUN')
light_data.energy = 5
light_data.angle = 0.08                    # harsh tropical shadows
light_data.color = (1.0, 0.94, 0.85)
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
scene.cycles.samples = 160
scene.cycles.use_denoising = True
scene.render.resolution_x = 1100
scene.render.resolution_y = 850
scene.world = bpy.data.worlds.new("w"); scene.world.use_nodes = True
bg = scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.5, 0.68, 0.95, 1.0)
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered", out)
