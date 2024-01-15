#! /usr/bin/env python3
#
# Routing classes

import math

import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from pcbflow import *


class Route(Turtle):
    def __init__(self, board, tt):
        self.tt = tt
        self.board = board

    def __repr__(self):
        return "<Route %d at %r>" % (len(self.tt), self.tt[0])

    def __len__(self):
        return len(self.tt)

    def r(self):
        return self.board.drc.channel() * (len(self.tt) - 1)

    def forward(self, d):
        [t.forward(d) for t in self.tt]
        return self

    def rpivot(self, a):
        # rotate all points clockwise by angle a
        s = math.sin(a)
        c = math.cos(a)
        (x0, y0) = self.tt[0].xy
        for i, t in enumerate(self.tt):
            x = t.xy[0] - x0
            y = t.xy[1] - y0
            nx = x * c - y * s
            ny = y * c + x * s
            t.xy = (x0 + nx, y0 + ny)
            t.path.append(t.xy)

    def lpivot(self, a):
        # rotate all points counter-clockwise by angle a
        s = math.sin(a)
        c = math.cos(a)
        tt = self.tt[::-1]
        (x0, y0) = tt[0].xy
        for i, t in enumerate(tt):
            x = t.xy[0] - x0
            y = t.xy[1] - y0
            nx = x * c - y * s
            ny = y * c + x * s
            t.xy = (x0 + nx, y0 + ny)
            t.path.append(t.xy)

    def right(self, a):
        if a < 0:
            return self.left(-a)
        fd = (self.tt[0].dir + a) % 360
        n = int(a + 1)
        ra = 2 * math.pi * a / 360
        for i in range(n):
            self.rpivot(-ra / n)
        for t in self.tt:
            t.dir = fd
        return self

    def left(self, a):
        if a < 0:
            return self.right(-a)
        fd = (self.tt[0].dir - a) % 360
        n = int(a + 1)
        ra = 2 * math.pi * a / 360
        for i in range(n):
            self.lpivot(ra / n)
        for t in self.tt:
            t.dir = fd
        return self

    def shimmy(self, d):
        if d == 0:
            return
        r = self.r()
        if abs(d) > r:
            a = 90
            f = abs(d) - r
        else:
            a = 180 * math.acos(1 - abs(d) / r) / math.pi
            f = 0
        if d > 0:
            self.left(a)
            self.forward(f)
            self.right(a)
        else:
            self.right(a)
            self.forward(f)
            self.left(a)
        return self

    def spread(self, d):
        c = self.board.drc.channel()
        n = len(self.tt) - 1
        for i, t in enumerate(self.tt[::-1]):
            i_ = n - i
            t.forward(c * i).left(90).forward(i_ * d).right(90).forward(c * i_)
        return self

    def join(self, other, ratio=0.0):
        assert 0 <= ratio <= 1
        st = self.tt[-1]
        ot = other.tt[0]

        (x0, y0) = ot.xy
        (x1, y1) = st.xy
        s2 = st.copy()
        s2.forward(1)
        (x2, y2) = s2.xy

        d = (y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1
        if d < 0:
            d += self.board.drc.channel()
        else:
            d -= self.board.drc.channel()
        self.shimmy(ratio * -d)
        other.shimmy((1 - ratio) * d)

        if st.is_behind(ot):
            extend(ot, self.tt)
        else:
            extend(st, other.tt)
        return Route(self.board, self.tt + other.tt)

    def meet(self, other):
        tu = ((other.tt[0].dir + 180) - self.tt[0].dir) % 360
        if tu < 180:
            self.right(tu)
        else:
            self.left(tu)
        (x, _) = self.tt[0].seek(other.tt[-1])
        self.shimmy(-x)
        d = self.tt[0].distance(other.tt[-1])
        self.forward(d)
        self.wire()
        self.board.nets += [
            ((a.part, a.name), (b.part, b.name))
            for (a, b) in zip(self.tt, other.tt[::-1])
        ]
        """
        for (a, b) in zip(self.tt, other.tt[::-1]):
            print(a.name, b.name, a.length + b.length)
        """

    def meet0(self, other):
        d = self.tt[0].distance(other.tt[0])
        c = self.board.drc.channel()
        r = c * (len(self.tt) - 1)
        l = math.sqrt(d**2 - r**2)
        dir_d = self.tt[0].direction(other.tt[0])
        a = math.acos(l / d)
        self.right(180 * (dir_d + a) / math.pi)
        self.forward(l)
        self.wire()

    def meet2(self, other):
        src = self.tt[0]
        dst = other.tt[-1]
        d = src.distance(dst)
        dir_d = DEGREES(src.direction(dst))

        self.right(dir_d)
        self.forward(d)
        self.wire()

        other.left(90 - dir_d).wire()
        self.board.nets += [
            ((a.part, a.name), (b.part, b.name))
            for (a, b) in zip(self.tt, other.tt[::-1])
        ]

    def split(self, n):
        a = Route(self.board, self.tt[:n])
        b = Route(self.board, self.tt[n:])
        return (a, b)

    def wire(self, layer=None, width=None):
        [t.wire(layer, width) for t in self.tt]
        return self

    def through(self):
        h = self.board.drc.via_drill + self.board.drc.clearance
        th = math.acos(self.board.drc.channel() / h)
        d = self.board.drc.via_drill / 2 + self.board.clearance
        a = h * math.sin(th)
        th_d = math.degrees(th)
        dst = {"GTL": "GBL", "GBL": "GTL"}[self.tt[0].layer]

        self.forward(d)
        for i, t in enumerate(self.tt):
            t.forward(i * a).right(th_d).forward(d).wire()
            t.via().set_layer(dst)
            t.forward(d).left(th_d).forward((len(self.tt) - 1 - i) * a)
        self.forward(d)
        self.wire()
        return self

    def shuffle(self, other, mp):
        h = self.board.drc.via_drill + self.board.drc.clearance  # / math.sqrt(2)
        th = math.acos(self.board.drc.channel() / h)
        d = self.board.drc.via_drill / 2 + self.board.drc.clearance
        a = h * math.sin(th)
        th_d = math.degrees(th)
        dst = {"GTL": "GBL", "GBL": "GTL"}[self.tt[0].layer]
        self.forward(d)
        othernames = {p.name: i for i, p in enumerate(other.tt)}
        newt = [None for _ in self.tt]
        for i, t in enumerate(self.tt):
            t.forward(i * a).right(th_d)
            t.forward(d)
            fa = othernames[mp[t.name]]
            newt[fa] = t
            t.forward(h * fa)
            t.wire()
            t.through()
            t.left(90)
        extend2(self.tt)
        self.tt = newt[::-1]
        self.forward(d)
        for i, t in enumerate(self.tt):
            t.left(th_d).forward((len(self.tt) - 1 - i) * a)
        self.wire()
        return self
