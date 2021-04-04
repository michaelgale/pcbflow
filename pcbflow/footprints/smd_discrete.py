#! /usr/bin/env python3
#
# SMD Resistor, Capacitor, Inductor discrete parts
#

from pcbflow import *


class Discrete2(Part):
    def escape(self, l0, l1):
        # Connections to GND and VCC
        [p.outside() for p in self.pads]
        self.pads[0].wvia(l0)
        self.pads[1].wvia(l1)


class C0402(Discrete2):
    family = "C"
    footprint = "0402"

    def place(self, dc):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(1.30 / 2)
            dc.rect(0.8, 0.8)
            self.pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(1.0, 0.5)
        dc.silko(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-1.2)
        else:
            dc.forward(1.2)
        self.label(dc, angle=dc.dir)
        dc.pop()

    def escape_2layer(self):
        # escape for 2-layer board (VCC on GTL, GND on GBL)
        self.pads[0].setname("VCC").w("o f 0.5").wire()
        self.pads[1].w("o -")


class C0603(Discrete2):
    family = "C"
    footprint = "0603"

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(1.70 / 2)
            dc.rect(1.0, 1.0)
            self.pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(1.6, 0.8)
        dc.silko(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-1.3)
        else:
            dc.forward(1.3)
        self.label(dc, angle=dc.dir)
        dc.pop()


class C1206(Discrete2):
    family = "C"
    footprint = "1206"

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(3.40 / 2)
            dc.rect(2.0, 2.0)
            self.pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(3.2, 1.6)
        dc.silko(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-1.8)
        else:
            dc.forward(1.8)
        self.label(dc, angle=dc.dir)
        dc.pop()


class R0402(C0402):
    family = "R"


class R0603(C0603):
    family = "R"


class R1206(C1206):
    family = "R"


class L0603(C0603):
    family = "L"


class L1206(C1206):
    family = "L"
