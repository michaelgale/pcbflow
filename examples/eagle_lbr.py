import math
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":

    brd = Board((50, 50))
    EaglePart(
        brd.DC((10, 10)),
        libraryfile="sparkfun.lbr",
        partname="USB-B-SMT",
        side="bottom",
    )
    EaglePart(brd.DC((10, 10)), libraryfile="sparkfun.lbr", partname="TSSOP-24")
    EaglePart(brd.DC((30, 25)), libraryfile="sparkfun.lbr", partname="ARDUINO_MINI")

    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "VCC")

    brd.save("%s" % (__file__[:-3]))

    print(brd.parts_str())
    print(brd.layer_net_str())
