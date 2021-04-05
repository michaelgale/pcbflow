import math
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((50, 30))
    brd.via_track_width = MILS(24)

    SOT23(brd.DC((10, 20)), side="top")
    SOT223(brd.DC((20, 20)), side="top")
    TSSOP14(brd.DC((30, 20)), side="top")
    QFN64(brd.DC((35, 10)), side="top")

    SOT23(brd.DC((5, 10)), side="bottom")
    SOT223(brd.DC((15, 10)), side="bottom")
    SOIC8(brd.DC((25, 10)), side="bottom")

    brd.outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    print(brd.parts_str())
    print(brd.nets_str())

    brd.save("%s" % (__file__[:-3]))
