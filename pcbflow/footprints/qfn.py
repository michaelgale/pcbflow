#! /usr/bin/env python3
#
# QFN parts
#

from pcbflow import *


class QFN64(PCBPart):
    def __init__(self, *args, **kwargs):
        self.family = "U"
        self.footprint = "QFN64"
        super().__init__(*args, **kwargs)

    def place(self, dc):
        # Ground pad
        g = 7.15 / 3
        for i in (-g, 0, g):
            for j in (-g, 0, g):
                dc.push()
                dc.forward(i)
                dc.left(90)
                dc.forward(j)
                dc.square(g - 0.5)
                self.smd_pad(dc)
                dc.via("GND")
                dc.pop()
        self.pads = self.pads[:1]

        # Silk outline of the package
        self.chamfered(dc, 9, 9)
        # self.chamfered(dc, 7.15, 7.15)

        for i in range(4):
            dc.left(90)
            dc.push()
            dc.forward(8.10 / 2)
            dc.forward(0.70 / 2)
            dc.right(90)
            dc.forward(7.50 / 2)
            dc.left(180)
            self.train(dc, 16, lambda: self.rpad(dc, 0.25, 0.70), 0.50)
            dc.pop()
