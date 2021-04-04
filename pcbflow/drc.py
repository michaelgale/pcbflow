#! /usr/bin/env python3
#
# Design Rules Check (DRC) 
#

from pcbflow import *

class DRC():

    def __init__(self):
        # Copper features
        self.trace_width = mil(8)
        self.via_drill = 0.5
        self.via_annular_ring = mil(8)
        self.via_track_width = mil(16)
        # Clearances
        self.clearance = mil(8)
        self.outline_clearance = mil(20)
        self.hole_clearance = mil(20)
        # Soldermask
        self.mask_vias = False
        self.mask_holes = True
        self.hole_mask = mil(16)
        self.soldermask_margin = mil(5)
        # Other
        self.bitmap_res = 0.04
        self.silk_width = mil(6)

    def channel(self):
        return self.trace_width + self.clearance

