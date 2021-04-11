#! /usr/bin/env python3
#
# Design Rules Check (DRC)
#

from pcbflow import *


class DRC:
    def __init__(self):
        # Copper features
        self.trace_width = MILS(8)
        self.via_drill = 0.5
        self.via_annular_ring = MILS(8)
        self.via_track_width = MILS(12)
        # Clearances
        self.clearance = MILS(8)
        self.outline_clearance = MILS(20)
        self.hole_clearance = MILS(20)
        # Soldermask
        self.mask_vias = False
        self.mask_holes = True
        self.hole_mask = MILS(16)
        self.soldermask_margin = MILS(3)
        # Other
        self.bitmap_res = 0.04
        self.silk_width = MILS(6)
        self.text_silk_width = MILS(6)

    def channel(self):
        return self.trace_width + self.clearance
