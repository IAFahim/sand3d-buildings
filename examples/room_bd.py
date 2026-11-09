"""A small room in the Bangladeshi idiom: exposed brick infill in a concrete frame.

Corner pilasters and a lintel band carry the RC-frame look; a parapet with concrete
coping; a rectangular door under a row of vent-block perforations; an arched window
with louvered wooden shutters on each side wall; the floor raised on a plinth.
Millimetres.
"""
import sand3d as s3d
from pathlib import Path

W, D, H, T = 3600, 2800, 3000, 250  # footprint, wall height, 250 mm brick wall


def room(door_w=900, door_h=2100, win_w=900, spring=1800):
    walls = s3d.shell(s3d.box("walls", W, D, H + 400), T, open="top bottom")  # +400 rises past the roof: a parapet
    front = walls.face("+X")
    s3d.pocket(walls, s3d.rect(door_w, door_h + 60), depth=T + 80,           # the door, floor to lintel
               on=front.move(0, door_h / 2 - 30))
    s3d.pocket(walls, s3d.rect(120, 120), depth=T + 80,                      # vent blocks above it
               on=[front.move(x, 2250) for x in range(-400, 401, 200)])
    for side in (walls.face("+Y"), walls.face("-Y")):                        # an arched window on each side
        s3d.pocket(walls, s3d.rect(win_w, spring - 900), depth=T + 80, on=side.move(0, (900 + spring) / 2))
        s3d.pocket(walls, s3d.circle(win_w), depth=T + 80, on=side.move(0, spring))
    s3d.material(walls, "concrete", color="#a34a32")                         # brick red

    shutters = s3d.at(s3d.box("slat", win_w - 80, 90, 12),                   # six louvers per window, mid-wall
                      on=[side.move(0, 1000 + i * 140).offset(-T / 2).turn(rx=30)
                          for side in (walls.face("+Y"), walls.face("-Y")) for i in range(6)])
    s3d.material(shutters, "walnut")

    pilasters = s3d.at(s3d.box("pilaster", 300, 300, H + 400),               # the frame shows at the corners
                       on=[s3d.Frame((W / 2 - 100, D / 2 - 100, 0)), s3d.Frame((W / 2 - 100, -D / 2 + 100, 0)),
                           s3d.Frame((-W / 2 + 100, D / 2 - 100, 0)), s3d.Frame((-W / 2 + 100, -D / 2 + 100, 0))])
    band = s3d.at(s3d.shell(s3d.box("band", W + 100, D + 100, 150), 60, open="top bottom"), z=2350)  # lintel ring
    coping = s3d.at(s3d.box("coping", W + 60, D + 60, 60), z=H + 400)
    s3d.material([pilasters, band, coping], "concrete", color="#b8b2a6")

    roof = s3d.at(s3d.box("roof", W - 2 * T, D - 2 * T, 130), z=H)
    s3d.material(roof, "concrete", color="#b8b2a6")
    floor = s3d.box("floor", W - 2 * T, D - 2 * T, T)                        # terracotta tile on the plinth
    s3d.material(floor, "ceramic", color="#a8623f")
    return s3d.assembly("room", walls, shutters, pilasters, band, coping, roof, floor)


s3d.empty_scene()
s3d.export(room(), str(Path(__file__).resolve().parents[1] / "models" / "room_bd.glb"))
print("OK - room_bd.glb exported")
