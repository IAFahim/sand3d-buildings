"""A Bangladeshi hamlet of tin houses: corrugated walls, rusty gable roofs, stilts.

Ridge along X; the door and windows cut as real cavities; the gable triangles clad
in tin; every house raised on timber posts over the paddy. Millimetres.
"""
import sand3d as s3d
from math import tan, sin, cos, radians
from pathlib import Path

PITCH = radians(28)


def tin_house(W=4200, D=3000, H=2100, plinth=450, ovh=500):
    parts = []
    # stilts, dug in past z = 0
    foot = [(x, y) for x in (-W / 2 + 200, 0, W / 2 - 200) for y in (-D / 2 + 200, D / 2 - 200)]
    parts.append(s3d.at(s3d.box("post", 160, 160, plinth + 60),
                        on=[s3d.Frame((fx, fy, -60)) for fx, fy in foot]))
    parts.append(s3d.at(s3d.box("floor", W, D, 80), z=plinth - 80))            # plank deck

    walls = s3d.at(s3d.shell(s3d.box("walls", W, D, H), 60, open="top bottom"), z=plinth)
    front, right, left = walls.face("+X"), walls.face("+Y"), walls.face("-Y")
    s3d.pocket(walls, s3d.rect(850, 2070), depth=140, on=front.move(0, 975))   # the door
    win_off = min(1350, W / 2 - 350)                                           # flanking the door, inside the wall
    s3d.pocket(walls, s3d.rect(600, 700), depth=140,                           # dark shutter windows
               on=[front.move(-win_off, 1500), front.move(win_off, 1500)])
    for side in (right, left):
        s3d.pocket(walls, s3d.rect(600, 700), depth=140, on=side.move(0, 1500))
    parts.append(walls)

    # gable triangles, clad in tin, from eave to ridge
    apex = tan(PITCH) * D / 2
    tri = s3d.poly([(-D / 2, 0), (D / 2, 0), (0, apex)])
    parts.append(s3d.extrude("gable_w", tri, 60, on=s3d.Frame((-W / 2, 0, plinth + H), normal=(1, 0, 0))))
    parts.append(s3d.extrude("gable_e", tri, 60, on=s3d.Frame((W / 2, 0, plinth + H), normal=(-1, 0, 0))))

    # the two roof planes, meeting at the ridge, eaves past the walls
    z_ridge = plinth + H + apex
    slope = (D / 2 + ovh) / cos(PITCH)
    drop = sin(PITCH) * slope / 2
    run = cos(PITCH) * slope / 2
    parts.append(s3d.at(s3d.box("roof_f", W + 2 * ovh, slope, 50),
                        on=s3d.Frame((0, run, z_ridge - drop), normal=(0, sin(PITCH), cos(PITCH)))))
    parts.append(s3d.at(s3d.box("roof_b", W + 2 * ovh, slope, 50),
                        on=s3d.Frame((0, -run, z_ridge - drop), normal=(0, -sin(PITCH), cos(PITCH)))))
    flat = [p for part in parts for p in (part if isinstance(part, list) else [part])]
    s3d.material([p for p in flat if "gable" in p.name or "roof" in p.name], "steel", color="#8a4a34")
    s3d.material(walls, "brushed_steel", color="#9aa3a8")
    s3d.material([p for p in flat if p.name.startswith(("post", "floor"))], "pine")
    return s3d.group("house", *parts)


s3d.empty_scene()
main = tin_house()
back = tin_house(W=3000, D=2400, H=1800, plinth=380)
s3d.transform(back, x=-3800, y=2700, rz=10)
shed = tin_house(W=2600, D=2000, H=1650, plinth=300)
s3d.transform(shed, x=3900, y=-2700, rz=-16)
s3d.export(s3d.group("hamlet", main, back, shed), str(Path(__file__).resolve().parents[1] / "models" / "tin_hamlet.glb"))
print("OK - tin_hamlet.glb exported")
