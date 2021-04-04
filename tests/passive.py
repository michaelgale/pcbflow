import math
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.via_track_width = mil(24)

    C0603(brd.DC((20, 20)).right(90), '0.1 uF', side="top")
    C0603(brd.DC((22, 20)).right(90), '0.1 uF', side="bottom")
    C0603(brd.DC((24, 20)).right(90), '0.1 uF', side="top").escape("GTL", "GTL")
    C0603(brd.DC((26, 20)).right(90), '0.1 uF', side="bottom").escape("GBL", "GBL")

    R0603(brd.DC((20, 10)).right(90), "4.7k", side="top")
    R0603(brd.DC((22, 10)).right(90), "4.7k", side="bottom")
    R0603(brd.DC((24, 10)).right(90), "4.7k", side="top").escape("GTL", "GTL")
    R0603(brd.DC((26, 10)).right(90), "4.7k", side="bottom").escape("GBL", "GBL")

    brd.outline()
    brd.fill_any("GTL", "GND")
    brd.fill_any("GBL", "GND")
    brd.save("%s" % (__file__[:-3]))
