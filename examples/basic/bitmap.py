import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.add_bitmap((10, 10), "fxlogo.png", scale=0.5)
    brd.add_bitmap((30, 10), "fxlogo.png", side="bottom", scale=0.33)
    brd.add_bitmap((10, 20), "fxlogo.png", scale=0.5, layer="GTL")
    brd.add_bitmap((25, 20), "fxlogo.png", scale=0.5, layer="GTL", keepout_box=True)
    brd.add_bitmap((30, 20), "fxlogo.png", side="bottom", layer="GBL", scale=0.33)
    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.save("%s" % (os.path.basename(__file__)[:-3]))
