import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.bitmap("fxlogo.png", 10, 15, scale=0.5)
    brd.bitmap("fxlogo.png", 30, 15, side="bottom", scale=0.33)
    brd.outline()
    brd.fill_any("GTL", "GND")
    brd.fill_any("GBL", "GND")
    brd.save("%s" % (__file__[:-3]))
