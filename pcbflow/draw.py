#! /usr/bin/env python3
#
# Turtle style drawing classes

import math

import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from pcbflow import *


class Turtle:
    def __repr__(self):
        return "<at (%.3f, %.3f) facing %.3f>" % (self.xy + (self.dir,))

    def w(self, s, layer="GTL"):
        tokens = s.split()
        cmds1 = {
            "i": self.inside,
            "o": self.outside,
            "-": lambda: self.wvia("GL2"),
            "+": lambda: self.wvia("GL3"),
            ".": lambda: self.wvia("GBL"),
            "/": self.through,
        }
        cmds2 = {"f": self.forward, "l": self.left, "r": self.right}

        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t in cmds1:
                cmds1[t]()
                i += 1
            else:
                cmds2[t](float(tokens[i + 1]))
                i += 2
        # self.wire(layer)
        return self

    def inside(self):
        pass

    def outside(self):
        pass

    def through(self):
        pass


class Draw(Turtle):
    def __init__(self, board, xy, dir=0, name=None):
        self.board = board
        self.xy = xy
        self.dir = dir
        self.stack = []
        self.part = None
        self.name = None
        self.newpath()
        self.width = board.drc.trace_width
        self.h = None
        self.length = 0
        self.defaults()

    def defaults(self):
        self.layer = "GTL"

    def _layers(self, side):
        if side == "top":
            return ["GTL", "GTS", "GTP"]
        else:
            return ["GBL", "GBS", "GBP"]

    def _silklayer(self, side):
        if side == "top":
            return "GTO"
        return "GBO"

    def setname(self, nm):
        self.name = nm
        return self

    def setwidth(self, w):
        self.width = w
        return self

    def setlayer(self, l):
        self.layer = l
        return self

    def newpath(self):
        self.path = [self.xy]
        return self

    def push(self):
        self.stack.append((self.xy, self.dir))
        return self

    def pop(self):
        (self.xy, self.dir) = self.stack.pop(-1)
        return self

    def copy(self):
        r = type(self)(self.board, self.xy, self.dir)
        r.h = self.h
        r.layer = self.layer
        r.name = self.name
        r.part = self.part
        r.width = self.width
        return r

    def forward(self, d):
        (x, y) = self.xy
        a = (self.dir / 360) * (2 * math.pi)
        (xd, yd) = (d * math.sin(a), d * math.cos(a))
        self.xy = (x + xd, y + yd)
        self.path.append(self.xy)
        return self

    def left(self, d):
        self.dir = (self.dir - d) % 360
        return self

    def right(self, d):
        self.dir = (self.dir + d) % 360
        return self

    def approach(self, d, other):
        assert ((self.dir - other.dir) % 360) in (90, 270)
        # Go forward to be exactly d away from infinite line 'other'
        (x0, y0) = self.xy
        (x1, y1) = other.xy
        o2 = other.copy()
        o2.forward(1)
        (x2, y2) = o2.xy
        self.forward(abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) - d)

    def seek(self, other):
        (dx, dy) = (other.xy[0] - self.xy[0], other.xy[1] - self.xy[1])
        a = (self.dir / 360) * (2 * math.pi)
        s = math.sin(a)
        c = math.cos(a)
        ox = dx * c - dy * s
        oy = dy * c + dx * s
        return (ox, oy)

    def goto(self, other):
        return self.goxy(*self.seek(other))

    def goxy(self, x, y):
        self.right(90)
        self.forward(x)
        self.left(90)
        self.forward(y)
        return self

    def is_behind(self, other):
        assert abs(self.dir - other.dir) < 0.0001, abs(self.dir - other.dir)
        (_, y) = self.seek(other)
        return y > 0

    def distance(self, other):
        return math.sqrt(
            (other.xy[0] - self.xy[0]) ** 2 + (other.xy[1] - self.xy[1]) ** 2
        )

    def direction(self, other):
        x = other.xy[0] - self.xy[0]
        y = other.xy[1] - self.xy[1]
        return math.atan2(x, y)

    def rect(self, w, h):
        self.push()
        self.forward(h / 2)
        self.right(90)
        self.forward(w / 2)

        self.newpath()
        self.right(90)
        self.forward(h)
        self.right(90)
        self.forward(w)
        self.right(90)
        self.forward(h)
        self.right(90)
        self.forward(w)
        self.pop()
        self.h = h  # used by inside, outside for pad escape
        return self

    def mark(self):
        self.board.layers["GTO"].add(sg.Point(self.xy).buffer(0.2))
        self.push()
        self.newpath()
        self.forward(0.3)
        self.silk()
        self.pop()
        return self

    def n_agon(self, r, n):
        # an n-agon approximating a circle radius r
        ea = 360 / n
        self.push()
        half_angle = math.pi / n
        half_edge = r * math.tan(half_angle)
        self.forward(r)
        self.right(90)

        self.newpath()
        for _ in range(n):
            self.forward(half_edge)
            self.right(ea)
            self.forward(half_edge)
        self.pop()

    def thermal(self, d):
        for i in range(4):
            self.forward(d)
            self.right(180)
            self.forward(d)
            self.right(90)
        return self

    def inside(self):
        self.right(180)
        self.forward(self.h / 2)
        return self

    def outside(self):
        self.forward(self.h / 2)
        return self

    def square(self, w):
        self.rect(w, w)

    def poly(self):
        return sg.Polygon(self.path)

    def pad(self):
        g = self.poly()
        if self.layer == "GTL":
            ly = ("GTL", "GTS", "GTP")
        elif self.layer == "GBL":
            ly = ("GBL", "GBS", "GBP")
        else:
            assert False, "Attempt to create pad in layer " + self.layer
        for n in ly:
            self.board.layers[n].add(g, self.name)

    def contact(self):
        g = sg.Polygon(self.path)
        for n in ("GTL", "GTS", "GBL", "GBS"):
            self.board.layers[n].add(g, self.name)

    def silk(self, side="top"):
        g = sg.LineString(self.path).buffer(self.board.drc.silk_width / 2)
        self.board.layers[self._silklayer(side)].add(g)

    def silko(self, side="top"):
        g = sg.LinearRing(self.path).buffer(self.board.drc.silk_width / 2)
        self.board.layers[self._silklayer(side)].add(g)

    def outline(self):
        g = sg.LinearRing(self.path)
        self.board.layers["GML"].add(g)

    def drill(self, d):
        self.board.add_drill(self.xy, d)

    def via(self, connect=None):
        dv = self.board.drc.via_drill / 2 + self.board.drc.via_annular_ring
        g = sg.Point(self.xy).buffer(dv)
        for n in ("GTL", "GP2", "GP3", "GBL"):
            self.board.layers[n].add(g, connect)
        if connect is not None:
            self.board.layers[self.layer].connected.append(g)
        self.board.add_drill(self.xy, self.board.drc.via_drill)
        gm = sg.Point(self.xy).buffer(dv + self.board.drc.soldermask_margin)
        if self.board.drc.mask_vias:
            self.board.layers["GTS"].add(gm)
            self.board.layers["GBS"].add(gm)
        self.newpath()
        return self

    def preview(self):
        return sg.LineString(self.path)

    def wire(self, layer=None, width=None):
        if layer is not None:
            self.layer = layer
        if width is not None:
            self.width = width
        if len(self.path) > 1:
            ls = sg.LineString(self.path)
            self.length += ls.length
            g = ls.buffer(self.width / 2)
            self.board.layers[self.layer].add(g, self.name)
            self.newpath()
        return self

    def wvia(self, layer, net=None):
        b = self.board
        self.forward(b.drc.clearance + b.drc.via_drill)
        self.wire(width=b.drc.via_track_width, layer=layer)
        self.via(net)

    def fan(self, l, dst):
        for a in (-45, 0, 45):
            self.copy().right(a).forward(l).wire(width=0.8).via(dst)

    def platedslot(self, buf):
        brd = self.board

        g1 = sg.LineString(self.path).buffer(buf)

        g2 = sg.LinearRing(g1.exterior.coords)
        brd.layers["GML"].add(g2)

        g3 = g1.buffer(0.3)
        brd.layers["GTS"].add(g3)

        g4 = g3.difference(g1.buffer(-0.05))
        for l in ("GTL", "GP2", "GP3", "GBL"):
            brd.layers[l].add(g4)

        strut_x = sa.scale(g4.envelope, yfact=0.15)
        strut_y = sa.scale(g4.envelope, xfact=0.15)
        struts = strut_x.union(strut_y)
        brd.layers["GTP"].add(g4.difference(struts))

    def meet(self, other):
        self.path.append(other.xy)
        return self.wire()

    def text(self, s, side="top"):
        (x, y) = self.xy
        self.board.layers[self._silklayer(side)].add(
            hershey.ctext(x, y, s, side=side, linewidth=self.board.drc.text_silk_width)
        )
        return self

    def ltext(self, s, side="top"):
        (x, y) = self.xy
        self.board.layers[self._silklayer(side)].add(
            hershey.ltext(x, y, s, side=side, linewidth=self.board.drc.text_silk_width)
        )

    def through(self):
        self.wire()
        dst = {"GTL": "GBL", "GBL": "GTL"}[self.layer]
        self.via().setlayer(dst)
        return self


class Drawf(Draw):
    def defaults(self):
        self.layer = "GBL"

    def left(self, a):
        return Draw.right(self, a)

    def right(self, a):
        return Draw.left(self, a)

    def goxy(self, x, y):
        return Draw.goxy(-x, y)
