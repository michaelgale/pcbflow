#! /usr/bin/env python3
#
# Crysal Oscillator parts
#

from pcbflow import *


class SMD_3225_4P(PCBPart):
    def __init__(self, *args, **kwargs):
        self.family = "Y"
        self.footprint = "4-SMD"
        super().__init__(*args, **kwargs)

    def place(self, dc):
        self.chamfered(dc, 2.8, 3.5, idoffset=(1.4, 0.2))

        for _ in range(2):
            dc.push()
            dc.goxy(-1.75 / 2, 2.20 / 2).right(180)
            self.train(dc, 2, lambda: self.rpad(dc, 1.2, 0.95), 2.20)
            dc.pop()
            dc.right(180)
        [p.set_name(nm) for p, nm in zip(self.pads, ["", "GND", "CLK", "VDD"])]
