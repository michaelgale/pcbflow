#! /usr/bin/env python3
#
# Design Rules Check (DRC) 
#

from pcbflow import *

class DRC():

    def __init__(self):
        self.trace_width = mil(8)
        self.trace_space = mil(8)
        self.via_drill = 0.5
        self.via_annular_ring = mil(8)
        self.via_space = mil(8)
        self.via_track_width = mil(16)
        self.mask_holes = True
        self.hole_mask = mil(16)
        self.hole_keepout = mil(20)
        self.keepout_space = mil(10)
        self.outline_space = mil(20)
        self.bitmap_res = 0.04
        self.silk_width = mil(6)
        self.mask_border = mil(5)


