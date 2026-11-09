"""A small room: concrete walls, oak floor, flat slab roof.

A door and two windows cut through the front wall (+X). Millimetres, as sand3d defaults.
"""
import sand3d as s3d
from pathlib import Path

W, D, H, T = 3600, 2800, 2600, 120  # footprint, wall height, wall thickness


def room(door_w=900, door_h=2100, win_w=900, win_h=1200, sill=900):
    walls = s3d.shell(s3d.box("walls", W, D, H), T, open="top bottom")  # a perimeter tube
    front = walls.face("+X")
    # The door, centred: the tool dips 60 below ground, so the wall clips it and the
    # opening lands exactly on the floor with no coincident faces for the boolean.
    s3d.pocket(walls, s3d.rect(door_w, door_h + 60), depth=T + 80, on=front.move(0, door_h / 2 - 30))
    # Two windows flanking it, 250 mm of wall in between, sitting on the sill.
    win_x = door_w / 2 + 250 + win_w / 2
    s3d.pocket(walls, s3d.rect(win_w, win_h), depth=T + 80,
               on=[front.move(-win_x, sill + win_h / 2), front.move(win_x, sill + win_h / 2)])
    s3d.material(walls, "concrete", color="#ded7c9")

    floor = s3d.box("floor", W - 2 * T, D - 2 * T, T)  # fits inside the tube
    s3d.material(floor, "oak")

    roof = s3d.at(s3d.box("roof", W + 240, D + 240, 140), z=H)  # 120 mm eaves all round
    s3d.material(roof, "concrete", color="#7d8288")
    return s3d.assembly("room", walls, floor, roof)


s3d.empty_scene()
s3d.export(room(), str(Path(__file__).resolve().parents[1] / "models" / "room.glb"))
print("OK - room.glb exported")
