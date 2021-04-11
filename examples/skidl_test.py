import os
import math
import glob
import shapely.geometry as sg

from pcbflow import *
from skidl import *


if __name__ == "__main__":
    brd = Board((55, 30))
    brd.add_inner_copper_layer(2)

    # Declare microcontroller
    mcu = Part(
        "DSP_Microchip_DSPIC33",
        "DSPIC33EP256MU806-xPT",
        footprint="TQFP-64_10x10mm_P0.5mm",
    )
    # Declare a generic 0603 capacitor
    cap = Part(
        "Device",
        "C",
        footprint="C_0603_1608Metric_Pad1.08x0.95mm_HandSolder",
        dest=TEMPLATE,
    )

    # Declare 3 instances of our generic capacitor with values
    c1 = cap(value="10uF")
    c2 = cap(value="0.1uF")
    c3 = cap(value="0.1uF")

    # Create GND and VDD nets
    vdd = Net("VDD")
    gnd = Net("GND")

    # Assign VDD and GND to our parts
    mcu["VDD"] += vdd
    mcu["VSS"] += gnd
    for c in [c1, c2, c3]:
        c[1] += vdd
        c[2] += gnd
    print(mcu["VDD"])
    # Assign a convenient reference to the default SKiDL circuit
    ckt = default_circuit

    print("Circuit\n  Parts: %d  Nets: %d" % (len(ckt.parts), len(ckt.nets)))

    # Assign part locations and instantiate pcbflow SkiPart(PCBPart) instances
    npos = [(35, 15), (25, 15), (45, 15), (37, 6.5)]
    sides = ["top", "bottom", "top", "bottom"]
    for part, pos, side in zip(ckt.parts, npos, sides):
        sp = SkiPart(brd.DC(pos), part, side=side)
        # "fanout" GND and VDD vias from parts with GND and VDD net connections
        sp.fanout(["VDD"])
        sp.fanout(["GND"], relative_to="inside")

    print(brd.parts_str())

    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.fill_layer("GP3", "VDD")

    brd.save("%s" % (__file__[:-3]))
