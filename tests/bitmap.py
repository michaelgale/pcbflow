import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.add_bitmap("fxlogo.png", 10, 10, scale=0.5)
    brd.add_bitmap("fxlogo.png", 30, 10, side="bottom", scale=0.33)
    brd.add_bitmap("fxlogo.png", 10, 20, scale=0.5, layer="GTL")
    brd.add_bitmap("fxlogo.png", 25, 20, scale=0.5, layer="GTL", keepout_box=True)
    brd.add_bitmap("fxlogo.png", 30, 20, side="bottom", layer="GBL", scale=0.33)
    brd.outline()
    brd.fill_any("GTL", "GND")
    brd.fill_any("GBL", "GND")
    brd.save("%s" % (__file__[:-3]))
