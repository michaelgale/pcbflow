#! /usr/bin/env python3
#
# SOT parts
#

from pcbflow import *


class SOT23(PCBPart):
    def __init__(self, *args, **kwargs):
        self.family = "U"
        self.footprint = "SOT23"
        super().__init__(*args, **kwargs)

    def place(self, dc):
        self.chamfered(dc, 3.0, 1.4)
        (w, h) = (1.0, 1.4)
        self.smd_pad(dc.copy().goxy(-0.95, -1.1).rect(w, h))
        self.smd_pad(dc.copy().goxy(0.95, -1.1).rect(w, h))
        self.smd_pad(dc.copy().goxy(0.00, 1.1).rect(w, h))
        [p.set_name(nm) for p, nm in zip(self.pads, ("1", "2", "3"))]


class SOT223(PCBPart):
    def __init__(self, *args, **kwargs):
        self.family = "U"
        self.footprint = "SOT223"
        super().__init__(*args, **kwargs)

    def place(self, dc):
        self.chamfered(dc, 6.30, 3.30)
        dc.push()
        dc.forward(6.2 / 2)
        dc.rect(3.6, 2.2)
        self.smd_pad(dc)
        dc.pop()

        dc.push()
        dc.left(90)
        dc.forward(4.60 / 2)
        dc.left(90)
        dc.forward(6.2 / 2)
        dc.left(90)
        self.train(dc, 3, lambda: self.rpad(dc, 1.20, 2.20), 2.30)
        dc.pop()

    def escape(self):
        # Returns (input, output) pads
        self.pads[2].w("i f 4").wire(width=0.8)
        self.pads[1].inside().fan(1.0, "GL2")
        self.pads[1].wire(width=0.8)
        return (self.pads[3], self.pads[0])


class SOT764(PCBPart):
    family = "U"

    def place(self, dc):
        self.chamfered(dc, 2.5, 4.5)
        # pad side is .240 x .950

        def p():
            dc.rect(0.240, 0.950)
            self.smd_pad(dc)

        for i in range(2):
            dc.push()
            dc.goxy(-0.250, (3.5 + 1.0) / 2)
            p()
            dc.pop()

            dc.push()
            dc.goxy(-(1.7 / 2 + 0.5), 3.5 / 2)
            dc.right(180)
            self.train(dc, 8, lambda: self.rpad(dc, 0.240, 0.950), 0.5)
            dc.pop()

            dc.push()
            dc.goxy(-0.250, -(3.5 + 1.0) / 2).right(180)
            p()
            dc.pop()
            dc.right(180)
