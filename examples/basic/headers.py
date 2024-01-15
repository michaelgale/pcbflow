import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    SIL(brd.DC((10, 5)).right(90), "2")
    SIL(brd.DC((10, 10)).right(90), "4")
    SIL_2mm(brd.DC((20, 5)).right(90), "2")
    SIL_2mm(brd.DC((20, 10)).right(90), "4")
    DIP8(brd.DC((15, 20)))
    DIP16(brd.DC((30, 15)), side="bottom")

    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.save("%s" % (os.path.basename(__file__)[:-3]))
