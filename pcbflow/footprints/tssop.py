#! /usr/bin/env python3
#
# TSSOP parts
#

from pcbflow import *


class TSSOP(PCBPart):
    def __init__(self, *args, N=None, footprint="TSSOP", **kwargs):
        self.family = "U"
        self.footprint = footprint
        self.N = N
        super().__init__(*args, **kwargs)

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, N=14, footprint="TSSOP14", **kwargs)


class TSSOP16(TSSOP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, N=16, footprint="TSSOP16", **kwargs)


class TSSOP20(TSSOP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, N=20, footprint="TSSOP20", **kwargs)


class TSSOP24(TSSOP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, N=24, footprint="TSSOP24", **kwargs)


class TSSOP28(TSSOP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, N=28, footprint="TSSOP28", **kwargs)
