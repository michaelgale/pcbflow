#! /usr/bin/env python3
#
# PCB part class
#

from collections import defaultdict
import re
import math
import csv

from PIL import Image
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so
import math

from pcbflow import *


def pretty_parts(nms):
    if len(nms[0]) < 2:
        return ""
    f = nms[0][0]
    nn = [int(nm[1:]) for nm in nms]
    ni = []
    while nn:
        seq = [i for (i, j) in zip(nn, range(nn[0], 9999)) if (i == j)]
        if len(seq) > 2:
            ni.append("{0}{1}-{2}".format(f, nn[0], nn[len(seq) - 1]))
            nn = nn[len(seq) :]
        else:
            ni.append("{0}{1}".format(f, nn[0]))
            nn = nn[1:]
    return ",".join(ni)


class PCBPart:
    """PCBPart base class
    All parts physically rendered on the PCB must inherit from this class.
    The __init__ method is somewhate complicated by having to anticipate
    the variety of scenarios from which it is inherited--i.e. missing or
    overlapping attributes, setting defaults, etc.
    All classes that derive from PCBPart must make a call to super().__init__
    so that it can be placed on the PCB (with its own place method) and
    ensure its ref des, family, height/width bounds are configured properly.
    """

    def __init__(self, dc, val=None, source=None, side="top", **kwargs):
        self.mfr = ""
        if "family" not in self.__dict__:
            self.family = ""
        if "footprint" not in self.__dict__:
            self.footprint = ""
        self.inBOM = True
        if "ref" in kwargs:
            self.id = kwargs["ref"]
            dc.board.parts[self.family].append(self)
        else:
            self.id = dc.board.assign(self)
        self.side = side.lower()
        self.pads = []
        if val is not None:
            self.val = val
        else:
            self.val = ""
        if source is not None:
            self.source = source
        else:
            self.source = {}

        dc.side = self.side
        self.board = dc.board
        self.center = dc.copy()
        for k, v in kwargs.items():
            self.__dict__[k] = v

        self.place(dc)
        self.bounds = self.get_bounds()

    def place(self, dc):
        raise NotImplementedError(
            "PCBPart class must be inherited from a class that implements the place method"
        )

    def __str__(self):
        s = []
        sp = ""
        if len(self.pads) > 0:
            sp = []
            for i, p in enumerate(self.pads):
                name = "?" if p.name is None else p.name
                sp.append(
                    "%3d: %s (%.2f, %.2f)"
                    % (i, name, better_float(p.xy[0]), better_float(p.xy[1]))
                )
        s.append(
            "Part[%s] %s %s %s(%6.2f, %6.2f) / %.0f deg %2d pads"
            % (
                self.id,
                self.footprint,
                self.val,
                self.side,
                *self.center.xy,
                self.center.dir,
                len(self.pads),
            )
        )
        s.append(col_str(sp))
        return "\n".join(s)

    def get_bounds(self):
        pbounds = []
        for pad in self.pads:
            pbounds.append(pad_bound(pad))
        maxb = max_bounds(pbounds, min_bound=0)
        return maxb

    def fanout(self, nets=None, length=None, relative_to="outside"):
        layer = "GTL" if self.side == "top" else "GBL"
        if nets is None:
            print(
                "WARNING: fanout for %s requires at least one net name to match against pad names"
                % (self.id)
            )
            return
        if isinstance(nets, str):
            nets = nets.split()
        elif not isinstance(nets, (list, tuple)):
            nets = [nets]
        for pad in self.pads:
            if pad.name is not None:
                if not pad.name == "" and pad.name in nets:
                    pad.push()
                    if relative_to == "inside":
                        pad.turtle("i").wvia(layer=layer, net=pad.name, length=length)
                    else:
                        pad.turtle("o").wvia(layer=layer, net=pad.name, length=length)
                    pad.pop()

    def text(self, dc, s):
        (x, y) = dc.xy
        dc.board.get_silk_layer(self.side).add(
            hershey.ctext(
                x, y, s, side=self.side, linewidth=dc.board.drc.text_silk_width
            )
        )

    def label(self, dc, angle=0):
        (x, y) = dc.xy
        gt = hershey.ctext(
            x, y, self.id, side=self.side, linewidth=dc.board.drc.text_silk_width
        )
        gt = sa.rotate(gt, angle)
        dc.board.get_silk_layer(self.side).add(gt)

    def minilabel(self, dc, s):
        dc.push()
        dc.rect(0.7, 0.7)
        dc.silk(side=self.side)
        dc.w("r 180 f 1.5")
        (x, y) = dc.xy
        dc.board.get_silk_layer(self.side).add(
            hershey.ctext(
                x, y, s, side=self.side, linewidth=dc.board.drc.text_silk_width
            )
        )
        dc.pop()
        dc.newpath()

    def notate(self, dc, s):
        (x, y) = dc.xy
        dc.board.get_silk_layer(self.side).add(
            hershey.text(
                x,
                y,
                s,
                scale=0.1,
                side=self.side,
                linewidth=dc.board.drc.text_silk_width,
            )
        )

    def chamfered(self, dc, w, h, drawid=True, idoffset=(0, 0)):
        nt = 0.4
        dc.push()
        dc.forward(h / 2)
        dc.left(90)
        dc.forward(w / 2 - nt)
        dc.right(180)
        dc.newpath()
        for e in (w - nt, h, w, h - nt):
            dc.forward(e)
            dc.right(90)
        dc.silk(side=self.side)
        dc.pop()

        dc.push()
        dc.forward(h / 2 + 0.5)
        dc.left(90)
        dc.forward(w / 2 + 0.5)
        dc.right(90)
        dc.goxy(*idoffset)
        (x, y) = dc.xy
        if drawid:
            dc.board.get_silk_layer(self.side).add(
                hershey.ctext(
                    x,
                    y,
                    self.id,
                    side=self.side,
                    linewidth=dc.board.drc.text_silk_width,
                )
            )
        dc.pop()

    def smd_pad(self, dc, ignore_paste=False):
        for layer in dc.board.get_smd_pad_layers(self.side, ignore_paste=ignore_paste):
            if layer.is_mask:
                g = dc.poly().buffer(dc.board.drc.soldermask_margin)
            else:
                g = dc.poly()
            layer.add(g)
        p = dc.copy()
        p.part = self.id
        self.pads.append(p)

    def rpad(self, dc, w, h):
        dc.right(90)
        dc.rect(w, h)
        self.smd_pad(dc)
        dc.left(90)

    def roundpad(self, dc, d, ignore_paste=False):
        (dc.w, dc.h) = (d, d)
        g = sg.Point(dc.xy).buffer(d / 2)
        for layer in dc.board.get_smd_pad_layers(self.side, ignore_paste=ignore_paste):
            if layer.is_mask:
                layer.add(g).buffer(dc.board.drc.soldermask_margin)
            else:
                layer.add(g)
        p = dc.copy()
        p.part = self.id
        self.pads.append(p)

    def train(self, dc, n, op, step):
        for i in range(n):
            op()
            dc.forward(step)

    def s(self, nm):
        if " " in nm:
            return [self.s(n) for n in nm.split()]
        return {p.name: p for p in self.pads}[nm]

    def pad(self, named=None):
        if " " in named:
            return [self.pad(n) for n in named.split()]
        if named is not None:
            return {p.name: p for p in self.pads}[named]
        raise KeyError("A valid pad name reference must be specified")
