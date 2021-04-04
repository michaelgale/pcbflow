import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    holexy = [
        (5, 5),
        (5, 25),
        (35, 5),
        (35, 25),
    ]
    for x, y in holexy:
        brd.hole((x, y), 2.0, 5)
    brd.outline()
    brd.fill_any("GTL", "GND")
    brd.fill_any("GBL", "GND")
    brd.save("%s" % (__file__[:-3]))
