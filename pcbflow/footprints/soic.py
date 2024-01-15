#! /usr/bin/env python3
#
# SOIC parts
#

from pcbflow import *


class SOIC(PCBPart):
    def __init__(self, *args, N=8, footprint="SOIC", **kwargs):
        self.family = "U"
        self.footprint = footprint
        self.N = N
        super().__init__(*args, **kwargs)

    def place(self, dc):
        self.chamfered(dc, self.A, self.B)
        for _ in range(2):
            dc.push()
            dc.forward(self.D / 2)
            dc.left(90)
            dc.forward(self.C / 2)
            dc.left(90)
            self.train(dc, self.N // 2, lambda: self.rpad(dc, 0.60, 2.20), 1.27)
            dc.pop()
            dc.right(180)


class SOIC8(SOIC):
    def __init__(self, *args, **kwargs):
        self.A = 4.0
        self.B = 5.0
        self.C = 5.90
        self.D = 3.81
        self.G = 3.0
        self.Z = 7.4
        super().__init__(*args, N=8, footprint="SOIC-8", **kwargs)
