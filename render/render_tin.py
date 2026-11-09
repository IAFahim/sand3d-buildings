import bpy, sys, functools
import mathutils

glb, out = sys.argv[1], sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "wide"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']

def corrugated(ob, base_a, base_b, ripple_pitch_mm, bump=0.35, rust=False, metallic=0.35, rough=0.8, noise_scale=4.0):
    nt = ob.data.materials[0].node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mapn = nt.nodes.new('ShaderNodeMapping')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'; wave.bands_direction = 'X'; wave.wave_profile = 'TRI'
    # object bbox width -> bands
    width = max(ob.dimensions) if not rust else max(ob.dimensions)
    wave.inputs['Scale'].default_value = ob.dimensions.x / (ripple_pitch_mm / 1000)
    wave.inputs['Distortion'].default_value = 0.0
    bump_n = nt.nodes.new('ShaderNodeBump')
    bump_n.inputs['Strength'].default_value = bump
    nt.links.new(tc.outputs['Generated'], mapn.inputs['Vector'])
    nt.links.new(mapn.outputs['Vector'], wave.inputs['Vector'])
    nt.links.new(wave.outputs['Fac'], bump_n.inputs['Height'])
    nt.links.new(bump_n.outputs['Normal'], bsdf.inputs['Normal'])
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = noise_scale
    noise.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Generated'], noise.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    stops = [(0.0, (*base_a, 1)), (0.35, (*base_b, 1))]
    if rust:
        stops = [(0.0, (0.10, 0.07, 0.05, 1)), (0.30, (0.22, 0.11, 0.08, 1)),
                 (0.55, (0.30, 0.13, 0.075, 1)), (0.75, (0.36, 0.17, 0.10, 1)),
                 (0.92, (0.45, 0.30, 0.20, 1))]
    while len(ramp.color_ramp.elements) < len(stops):
        ramp.color_ramp.elements.new(0.5)
    for el, (pos, col) in zip(ramp.color_ramp.elements, stops):
        el.position = pos; el.color = col
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

for ob in meshes:
    if ob.name.startswith("roof"):
        corrugated(ob, (0, 0, 0), (0, 0, 0), 75, bump=0.8, rust=True, metallic=0.15, rough=0.9, noise_scale=5.0)
    elif ob.name.startswith("gable"):
        corrugated(ob, (0, 0, 0), (0, 0, 0), 75, bump=0.5, rust=True, metallic=0.15, rough=0.9, noise_scale=5.0)
    elif ob.name.startswith("walls"):
        corrugated(ob, (0.24, 0.28, 0.31), (0.36, 0.40, 0.43), 75, bump=0.9, metallic=0.55, rough=0.35, noise_scale=4.0)
    elif ob.name.startswith(("post", "floor")):
        nt = ob.data.materials[0].node_tree
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (0.32, 0.22, 0.13, 1)
        bsdf.inputs['Roughness'].default_value = 0.9

# ground: the paddy
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.062))
grass = bpy.data.objects["Plane"]
gm = bpy.data.materials.new("grass"); gm.use_nodes = True
gb = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
gb.inputs['Roughness'].default_value = 1.0
gnoise = gm.node_tree.nodes.new('ShaderNodeTexNoise')
gnoise.inputs['Scale'].default_value = 10.0
gramp = gm.node_tree.nodes.new('ShaderNodeValToRGB')
gramp.color_ramp.elements[0].color = (0.06, 0.15, 0.04, 1)
gramp.color_ramp.elements[1].color = (0.14, 0.26, 0.06, 1)
gm.node_tree.links.new(gnoise.outputs['Fac'], gramp.inputs['Fac'])
gm.node_tree.links.new(gramp.outputs['Color'], gb.inputs['Base Color'])
grass.data.materials.append(gm)

bs_all = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
center = functools.reduce(lambda a, b: a + b, bs_all) / len(bs_all)
radius = max((center - b).length for b in bs_all)

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 35 if mode == "wide" else 40
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
if mode == "wide":     # across the paddy, like the photograph
    d = mathutils.Vector((1.05, -1.65, 0.15)).normalized()
    cam.location = center + d * radius * 1.9
    aim = center + mathutils.Vector((0, 0, 0.3))
    sun_dir = mathutils.Vector((1.2, -0.8, 1.5))
else:                  # closer three-quarter of the main house
    d = mathutils.Vector((1.5, -1.0, 0.30)).normalized()
    cam.location = mathutils.Vector((2.4, -7.6, 3.2))
    aim = mathutils.Vector((-0.4, 0.1, 1.2))
    sun_dir = mathutils.Vector((1.4, -1.0, 1.3))
cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

light_data = bpy.data.lights.new("key", 'SUN')
light_data.energy = 2.0
light_data.angle = 0.35                     # hazy, soft edges
light_data.color = (1.0, 0.96, 0.9)
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
scene.render.resolution_x = 1280
scene.render.resolution_y = 800
scene.world = bpy.data.worlds.new("w"); scene.world.use_nodes = True
bg = scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.72, 0.76, 0.82, 1.0)
bg.inputs[1].default_value = 0.85   # monsoon haze
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered", out)
