#! /usr/bin/env python3
#
# Special Connector parts
#

from pcbflow import *


class HDMI(PCBPart):
    def __init__(self, *args, **kwargs):
        self.family = "J"
        self.mfr = "HDMI-001"
        self.source = {"LCSC": "C138388"}
        self.footprint = "HDMI"
        super().__init__(*args, **kwargs)

    def place(self, dc):
        self.chamfered(dc, 15, 11.1)

        def mounting(dc, l):
            dc.push()
            dc.newpath()
            dc.forward(l / 2)
            dc.right(180)
            dc.forward(l)
            dc.platedslot(0.5)
            dc.pop()

        # mounting(dc, 2)
        dc.push()
        dc.right(90)
        dc.forward(4.5)
        dc.left(90)
        dc.forward(5.35)
        dc.left(90)
        self.train(dc, 19, lambda: self.rpad(dc, 0.30, 2.60), 0.50)
        dc.pop()

        dc.right(90)
        dc.forward(14.5 / 2)
        dc.left(90)
        dc.forward(5.35 + 1.3 - 2.06)
        dc.right(180)

        def holepair():
            dc.push()
            mounting(dc, 2.8 - 1)
            dc.forward(5.96)
            mounting(dc, 2.2 - 1)
            dc.pop()

        holepair()
        dc.right(90)
        dc.forward(14.5)
        dc.left(90)
        holepair()
        dc.forward(5.96 + 3.6)
        dc.left(90)

        dc.newpath()
        dc.forward(14.5)
        dc.silk()

    def escape(self):
        board = self.board
        gnd = (1, 4, 7, 10, 13, 16)
        for g, p in zip(gnd, ["TMDS2", "TMDS1", "TMDS0", "TMDS_CLK"]):
            self.pads[g].set_name("GND")
            self.pads[g - 1].set_name(p + "_P")
            self.pads[g + 1].set_name(p + "_N")

        for g in gnd:
            self.pads[g].w("i -")

        def pair(g):
            p = self.pads
            return self.board.enriverPair((p[g - 1], p[g + 1]))

        return ([pair(g) for g in gnd[:4]], self.pads[18])
