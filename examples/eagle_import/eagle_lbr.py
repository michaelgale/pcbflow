import math
import os
import geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((50, 50))
    EaglePart(brd.DC((10, 40)), libraryfile="sparkfun.lbr", partname="TSSOP-24")
    EaglePart(brd.DC((35, 34)), libraryfile="sparkfun.lbr", partname="ARDUINO_MINI")
    uc = EaglePart(brd.DC((40, 9)), libraryfile="sparkfun.lbr", partname="TQFP64")
    usb_con = EaglePart(
        brd.DC((10, 10)), libraryfile="sparkfun.lbr", partname="USB-B-SMT", side="top"
    )
    usb_con.pad("D-").turtle("r 90 f 5 l 90 f 10").wire(width=0.25)

    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "VCC")

    brd.save("%s" % (os.path.basename(__file__)[:-3]))

    print(brd.parts_str())
    print(brd.layer_net_str())
