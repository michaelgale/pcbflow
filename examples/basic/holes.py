import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    holes = [
        (5, 5),
        (5, 25),
        (35, 5),
        (35, 25),
    ]
    for hole in holes:
        brd.add_hole(hole, 2.0)
    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.save("%s" % (os.path.basename(__file__)[:-3]))
