#! /usr/bin/env python3
#
# SMD Resistor, Capacitor, Inductor discrete parts
#

from pcbflow import *


class Discrete2(PCBPart):
    def assign_pads(self, pad1=None, pad2=None):
        layer = "GTL" if self.side == "top" else "GBL"
        if pad1 is not None:
            self.pads[0].set_name(pad1)
        if pad2 is not None:
            self.pads[1].set_name(pad2)
        return self


class C0402(Discrete2):
    def __init__(self, *args, family="C", **kwargs):
        self.family = family
        self.footprint = "0402"
        super().__init__(*args, **kwargs)

    def place(self, dc):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(1.0 / 2)
            dc.rect(0.6, 0.6)
            self.smd_pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(2.5, 1.5)
        dc.silk(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-1.5)
        else:
            dc.forward(1.5)
        self.label(dc, angle=dc.dir)
        dc.pop()

    def escape_2layer(self):
        # escape for 2-layer board (VCC on GTL, GND on GBL)
        self.pads[0].set_name("VCC").w("o f 0.5").wire()
        self.pads[1].w("o -")


class C0603(Discrete2):
    def __init__(self, *args, family="C", **kwargs):
        self.family = family
        self.footprint = "0603"
        super().__init__(*args, **kwargs)

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(1.60 / 2)
            dc.rect(1.0, 1.0)
            self.smd_pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(3.5, 1.9)
        dc.silk(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-1.7)
        else:
            dc.forward(1.7)
        self.label(dc, angle=dc.dir)
        dc.pop()


class C0805(Discrete2):
    def __init__(self, *args, family="C", **kwargs):
        self.family = family
        self.footprint = "0805"
        super().__init__(*args, **kwargs)

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(2.0 / 2)
            dc.rect(1.5, 1.0)
            self.smd_pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(3.9, 2.4)
        dc.silk(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-2)
        else:
            dc.forward(2)
        self.label(dc, angle=dc.dir)
        dc.pop()


class C1206(Discrete2):
    def __init__(self, *args, family="C", **kwargs):
        self.family = family
        self.footprint = "1206"
        super().__init__(*args, **kwargs)

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(3.0 / 2)
            dc.rect(1.8, 1.2)
            self.smd_pad(dc)
            dc.pop()

        # Silk outline of the package
        dc.rect(5.1, 2.7)
        dc.silk(side=self.side)
        dc.push()
        if dc.dir == 90:
            dc.forward(-2.1)
        else:
            dc.forward(2.1)
        self.label(dc, angle=dc.dir)
        dc.pop()


class R0402(C0402):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="R", **kwargs)


class R0603(C0603):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="R", **kwargs)


class R0805(C0805):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="R", **kwargs)


class R1206(C1206):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="R", **kwargs)


class L0402(C0402):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="L", **kwargs)


class L0603(C0603):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="L", **kwargs)


class L0805(C0805):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="L", **kwargs)


class L1206(C1206):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, family="L", **kwargs)
