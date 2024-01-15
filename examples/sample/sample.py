import math
import optparse
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((55, 30))
    brd.add_inner_copper_layer(2)
    brd.add_named_rect((27, 25), (40, 10), "GP2", "GND")

    brd.add_part((5, 15), HDMI, side="top", rot=90, family="J")
    brd.add_part((32, 15), QFN64, side="top")
    rx = brd.add_part((15, 18), R0603, side="top")
    ry = brd.add_part((15, 12), R0603, side="top", val="4.7k")
    brd.add_part((15, 25), R0603, side="top", val="200", rot=90).assign_pads(
        "VCC", None
    ).fanout()
    C0603(brd.DC((35, 23)), "0.1 uF", side="top").assign_pads("GND", "VCC").fanout(
        ["VCC", "GND"]
    )
    C0603(brd.DC((41, 22)), "0.1 uF", side="bottom").assign_pads("GND", None).fanout(
        ["VCC", "GND"]
    )
    C0603(brd.DC((35, 7)).right(90), "0.1 uF", side="top").assign_pads(
        "VCC", "GND"
    ).fanout("VDD GND")
    C0603(brd.DC((42, 8)).right(90), "0.1 uF", side="bottom").assign_pads(
        "VCC", None
    ).fanout("VCC")

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
        usb_con.pad(p).turtle("R90 f2 r 45 f1 L45 f 2 .GBL f 2").wire()
    rx.pads[1].turtle("o f5 l45 f1.02 r45 f3 > U1-1").wire()
    ry.pads[1].turtle("o f5 l45 f2 l45 .GP3 f2 .GTL r45 f4 > U1-2").wire()

    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "VCC")
    brd.fill_layer("GP2", "VCC")
    brd.fill_layer("GP3", "GND")

    print(brd.parts_str())
    print(brd.layer_net_str())

    brd.save("%s" % (os.path.basename(__file__)[:-3]))
