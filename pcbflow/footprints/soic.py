#! /usr/bin/env python3
#
# SOIC parts
#

from pcbflow import *


class SOIC(Part):
    family = "U"
    footprint = "SOIC"

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
    N = 8
    footprint = "SOIC-8"

    A = 4.0
    B = 5.0
    C = 5.90
    D = 3.81
    G = 3.0
    Z = 7.4
