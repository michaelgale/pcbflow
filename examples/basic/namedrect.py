import math
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.add_outline()
    brd.add_named_rect((5, 25), (15, 20), "GTL", "ABC")
    brd.add_named_rect((5, 15), (25, 3), "GTL", "VCC")
    brd.add_named_rect((15, 25), (35, 20), "GBL", "GND")
    brd.add_named_rect((8, 15), (35, 3), "GBL", "VCC")
    brd.fill_layer("GTL", "VCC")
    brd.fill_layer("GBL", "GND")
    brd.save("%s" % (os.path.basename(__file__)[:-3]))
