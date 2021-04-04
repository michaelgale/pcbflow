#! /usr/bin/env python3
#
# TSSOP parts
#

from pcbflow import *


class TSSOP(Part):
    family = "U"
    footprint = "TSSOP"

    def place(self, dc):
        self.chamfered(dc, 4.4, {14: 5.0, 20: 6.5}[self.N])
        P = self.N // 2
        e = 0.65
        for _ in range(2):
            dc.push()
            dc.forward(e * (P - 1) / 2)
            dc.left(90)
            dc.forward((4.16 + 1.78) / 2)
            dc.left(90)
            self.train(dc, P, lambda: self.rpad(dc, 0.42, 1.78), e)
            dc.pop()
            dc.right(180)


class TSSOP14(TSSOP):
    N = 14
    footprint = "TSSOP14"

class TSSOP16(TSSOP):
    N = 16
    footprint = "TSSOP16"

class TSSOP20(TSSOP):
    N = 20
    footprint = "TSSOP20"

class TSSOP24(TSSOP):
    N = 24
    footprint = "TSSOP24"

