import math
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((55, 30))

    # These are the same:
    # HDMI(brd.DC((5, 15)).right(90), side="top")
    # brd.add_part((5, 15), HDMI, side="top", rot=90)

    brd.add_part((5, 15), HDMI, side="top", rot=90)
    brd.add_part((32, 15), QFN64, side="top")
    brd.add_part((15, 18), R0603, side="top")
    brd.add_part((15, 12), R0603, side="top", val="4.7k")
    brd.add_part((15, 25), R0603, side="top", val="200", rot=90).fanout("VCC", None)
    C0603(brd.DC((35, 23)), "0.1 uF", side="top").fanout("GND", "VCC")
    C0603(brd.DC((41, 22)), "0.1 uF", side="bottom").fanout("GND", None)
    C0603(brd.DC((35, 7)).right(90), "0.1 uF", side="top").fanout("VCC", "GND")
    C0603(brd.DC((42, 8)).right(90), "0.1 uF", side="bottom").fanout("VCC", None)

    for x in range(5):
        brd.add_part((5 + x * 3, 4), C0402, side="top")

    brd.add_part((25, 25), SOT23, side="bottom")
    brd.add_part((20, 8), SOT223, side="bottom")
    brd.add_part((35, 5), SOIC8, side="bottom")
    usb_con = EaglePart(
        brd.DC((50, 15)).right(180),
        libraryfile="sparkfun.lbr",
        partname="USB-B-SMT",
        side="top",
    )
    for p in ["D+", "D-"]:
        usb_con.pad(p).turtle("R90 f2 r 45 f1 L45 f 2 v GBL f 2").wire()

    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "VCC")

    brd.save("%s" % (__file__[:-3]))

    print(brd.parts_str())
    print(brd.layer_net_str())
