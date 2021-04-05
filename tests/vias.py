import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.DC((10, 10)).via()
    brd.DC((20, 10)).via()
    brd.DC((10, 20)).via()
    brd.DC((20, 20)).via()
    brd.outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.save("%s" % (__file__[:-3]))
