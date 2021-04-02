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


class Layer:
    def __init__(self, desc, function):
        self.polys = []
        self.desc = desc
        self.function = function
        self.connected = []
        self.p = None

    def add(self, o, nm=None):
        self.polys.append((nm, o.simplify(0.001, preserve_topology=False)))
        self.p = None

    def preview(self):
        if self.p is None:
            self.p = so.unary_union([p for (_, p) in self.polys])
        return self.p

    def paint(self, bg, include, r):
        # Return the intersection of bg with the current polylist
        # touching the included, avoiding the others by distance r
        ingrp = so.unary_union([bg] + [o for (nm, o) in self.polys if nm == include])
        exgrp = so.unary_union([o for (nm, o) in self.polys if nm != include])
        self.powered = so.unary_union(ingrp).difference(exgrp.buffer(r))
        return exgrp.union(self.powered)

    def fill(self, bg, include, d):
        self.polys = [("filled", self.paint(bg, include, d))]

    def save(self, f):
        surface = self.preview()
        g = Gerber(f, self.desc)
        g.file_function(self.function)
        def renderpoly(g, po):
            if type(po) == sg.MultiPolygon:
                [renderpoly(g, p) for p in po]
                return
            # Subdivide a poly if it has holes
            if len(po.interiors) == 0:
                g.poly(po.exterior.coords)
            else:
                x0 = min([x for (x, y) in po.exterior.coords])
                x1 = max([x for (x, y) in po.exterior.coords])
                y0 = min([y for (x, y) in po.exterior.coords])
                y1 = max([y for (x, y) in po.exterior.coords])
                xm = (x0 + x1) / 2
                eps = 0.005
                # eps = 0.000
                renderpoly(g, po.intersection(sg.box(x0, y0, xm + eps, y1)))
                renderpoly(g, po.intersection(sg.box(xm - eps, y0, x1, y1)))

        if isinstance(surface, sg.Polygon):
            renderpoly(g, surface)
        else:
            [renderpoly(g, po) for po in surface]
        g.finish()

    def povray(self, f, prefix="polygon {", mask=None, invert=False):
        surface = self.preview()
        if invert:
            surface = mask.difference(surface)
        elif mask is not None:
            surface = surface.intersection(mask)

        def renderpoly(po):
            if type(po) == sg.MultiPolygon:
                [renderpoly(p) for p in po]
                return
            allc = [po.exterior.coords] + [c.coords for c in po.interiors]
            total = sum([len(c) for c in allc])
            f.write(prefix)
            f.write("\n%d\n" % total)
            for c in allc:
                f.write(" ".join(["<%f,%f>" % (x, y) for (x, y) in c]) + "\n")
            f.write("}\n")

        if isinstance(surface, sg.Polygon):
            renderpoly(surface)
        else:
            [renderpoly(po) for po in surface]


class OutlineLayer:
    def __init__(self, desc):
        self.lines = []
        self.desc = desc

    def add(self, o):
        self.lines.append(o)

    def union(self, o):
        po = sg.Polygon(self.lines[0]).union(o.buffer(0))
        self.lines = [po.exterior]

    def remove(self, o):
        po = sg.Polygon(self.lines[0]).difference(o.buffer(0))
        self.lines = [po.exterior]

    def save(self, f):
        g = Gerber(f, self.desc)
        for ls in self.lines:
            g.linestring(ls.coords)
        g.finish()


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
        self.width = board.trace
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
        # Return position of other in our frame as (x, y) so that
        #     forward(y)
        #     right(90)
        #     forward(x)
        # moves to the other

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
        g = sg.LineString(self.path).buffer(self.board.silk / 2)
        self.board.layers[self._silklayer(side)].add(g)

    def silko(self, side="top"):
        g = sg.LinearRing(self.path).buffer(self.board.silk / 2)
        self.board.layers[self._silklayer(side)].add(g)

    def outline(self):
        g = sg.LinearRing(self.path)
        self.board.layers["GML"].add(g)

    def drill(self, d):
        self.board.drill(self.xy, d)

    def via(self, connect=None):
        g = sg.Point(self.xy).buffer(self.board.via / 2)
        for n in ("GTL", "GP2", "GP3", "GBL"):
            self.board.layers[n].add(g, connect)
        if connect is not None:
            self.board.layers[connect].connected.append(g)
        self.board.drill(self.xy, self.board.via_hole)
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

    def wvia(self, l):
        b = self.board
        self.forward(b.via_space + b.via / 2)
        self.wire(width=b.via_track_width, layer=l)
        self.via(l)

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
        self.board.layers[self._silklayer(side)].add(hershey.ctext(x, y, s))
        return self

    def ltext(self, s, side="top"):
        (x, y) = self.xy
        self.board.layers[self._silklayer(side)].add(hershey.ltext(x, y, s))

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


class River(Turtle):
    def __init__(self, board, tt):
        self.tt = tt
        self.board = board
        self.c = self.board.c

    def __repr__(self):
        return "<River %d at %r>" % (len(self.tt), self.tt[0])

    def __len__(self):
        return len(self.tt)

    def r(self):
        return self.c * (len(self.tt) - 1)

    def forward(self, d):
        [t.forward(d) for t in self.tt]
        return self

    def rpivot(self, a):
        # rotate all points clockwise by angle a
        s = math.sin(a)
        c = math.cos(a)
        (x0, y0) = self.tt[0].xy
        for (i, t) in enumerate(self.tt):
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
        for (i, t) in enumerate(tt):
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
        c = self.board.trace + self.board.space
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
            d += self.c
        else:
            d -= self.c
        self.shimmy(ratio * -d)
        other.shimmy((1 - ratio) * d)

        if st.is_behind(ot):
            extend(ot, self.tt)
        else:
            extend(st, other.tt)
        return River(self.board, self.tt + other.tt)

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
        c = self.board.trace + self.board.space
        r = c * (len(self.tt) - 1)
        l = math.sqrt(d ** 2 - r ** 2)
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
        a = River(self.board, self.tt[:n])
        b = River(self.board, self.tt[n:])
        return (a, b)

    def wire(self, layer=None, width=None):
        [t.wire(layer, width) for t in self.tt]
        return self

    def through(self):
        # print(self.tt[0].distance(self.tt[-1]))
        h = self.board.via + self.board.via_space
        th = math.acos(self.c / h)
        d = self.board.via / 2 + self.board.via_space
        a = h * math.sin(th)
        th_d = math.degrees(th)
        dst = {"GTL": "GBL", "GBL": "GTL"}[self.tt[0].layer]

        self.forward(d)
        for i, t in enumerate(self.tt):
            t.forward(i * a).right(th_d).forward(d).wire()
            t.via().setlayer(dst)
            t.forward(d).left(th_d).forward((len(self.tt) - 1 - i) * a)
        self.forward(d)
        self.wire()
        return self

    def shuffle(self, other, mp):
        # print(self.tt[0].distance(self.tt[-1]))
        h = self.board.via + self.board.via_space  # / math.sqrt(2)
        th = math.acos(self.c / h)
        d = self.board.via / 2 + self.board.via_space
        a = h * math.sin(th)
        th_d = math.degrees(th)
        dst = {"GTL": "GBL", "GBL": "GTL"}[self.tt[0].layer]

        # print('         mp', mp)
        # print('   original', [t.name for t in self.tt])
        # print('      other', [t.name for t in other.tt])
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
        # print('       newt', [t.name for t in newt])
        self.tt = newt[::-1]
        self.forward(d)
        for i, t in enumerate(self.tt):
            t.left(th_d).forward((len(self.tt) - 1 - i) * a)
        self.wire()
        return self


class Board:
    def __init__(self, size, trace, space, via_hole, via, via_space, silk):
        self.size = size
        self.trace = trace
        self.space = space
        self.via_hole = via_hole
        self.via = via
        self.via_space = via_space
        self.via_track_width = trace
        self.silk = silk
        self.parts = defaultdict(list)
        self.holes = defaultdict(list)
        self.npth = defaultdict(list)
        self.keepouts = []

        self.c = trace + space  # track spacing, used everywhere

        self.counters = defaultdict(lambda: 0)
        self.nets = []

        self.rules = {
            "mask_holes": True,
            "hole_mask": mil(16),
            "hole_keepout": mil(20),
        }

        layers = [
            ("GTP", "Top Paste", "Paste,Top"),
            ("GTO", "Top Silkscreen", "Legend,Top"),
            ("GTS", "Top Solder Mask", "Soldermask,Top"),
            ("GTL", "Top Copper", "Copper,L1,Top"),
            ("GP2", "Inner Copper Layer 2", "Copper,L2,Inr"),
            ("GP3", "Inner Copper Layer 3", "Copper,L3,Inr"),
            ("GBL", "Bottom Copper", "Copper,L4,Bot"),
            ("GBS", "Bottom Solder Mask", "Soldermask,Bot"),
            ("GBO", "Bottom Silkscreen", "Legend,Bot"),
            ("GBP", "Bottom Paste", "Paste,Bot"),
        ]
        self.layers = {id: Layer(desc, fn) for (id, desc, fn) in layers}
        self.layers["GML"] = OutlineLayer("Mechanical")

    def boundary(self, r=0):
        x0, y0 = (-r, -r)
        x1, y1 = self.size
        x1 += r
        y1 += r
        return sg.LinearRing([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def outline(self):
        self.layers["GML"].add(self.boundary())

    def oversize(self, r):
        self.layers["GML"].add(self.boundary(r))
        sr = self.silk / 2
        g = self.boundary(1.1 * sr).buffer(sr)
        self.layers["GTO"].add(g.buffer(0))

    def hole(self, xy, inner, outer=None, show_outline=False):
        self.npth[inner].append(xy)
        # self.drill(xy, inner)
        if outer is not None and show_outline:
            g = sg.LinearRing(sg.Point(xy).buffer(outer / 2).exterior).buffer(
                self.silk / 2
            )
            self.layers["GTO"].add(g)
        self.keepouts.append(sg.Point(xy).buffer(inner / 2 + self.rules["hole_keepout"]))
        gm = sg.Point(xy).buffer(inner / 2 + self.rules["hole_mask"])
        if self.rules["mask_holes"]:
            self.layers["GTS"].add(gm)
            self.layers["GBS"].add(gm)

    def drill(self, xy, diam):
        self.holes[diam].append(xy)

    def annotate(self, x, y, s):
        self.layers["GTO"].add(hershey.ctext(x, y, s))

    def DC(self, xy, d=0):
        return Draw(self, xy, d)

    def DCf(self, xy, d=0):
        return Drawf(self, xy, d)

    def fill(self):
        ko = so.unary_union(self.keepouts)
        g = sg.box(0, 0, self.size[0], self.size[1]).buffer(-0.2).difference(ko)
        self.layers["GL2"].fill(g, "GL2", self.via_space)
        self.layers["GL3"].fill(g, "GL3", self.via_space)

    def fill_any(self, layer, include):
        ko = so.unary_union(self.keepouts)
        g = self.body().buffer(-0.2).difference(ko)
        la = self.layers[layer]

        d = max(self.space, self.via_space)
        notouch = so.unary_union([o for (nm, o) in la.polys if nm != include])
        self.layers[layer].add(g.difference(notouch.buffer(d)), include)

    def addnet(self, a, b):
        self.nets.append(((a.part, a.name), (b.part, b.name)))

    def body(self):
        # Return the board outline with holes and slots removed.
        # This is the shape of the resin subtrate.
        gml = self.layers["GML"].lines
        mask = sg.Polygon(gml[-1], gml[:-1])
        for d, xys in self.holes.items():
            if d > 0.3:
                hlist = so.unary_union([sg.Point(xy).buffer(d / 2) for xy in xys])
                mask = mask.difference(hlist)
        return mask

    def substrate(self):
        substrate = Layer(None, None)
        gml = self.layers["GML"].lines
        mask = sg.Polygon(gml[-1], gml[:-1])
        for d, xys in self.holes.items():
            if d > 0.3:
                hlist = so.unary_union([sg.Point(xy).buffer(d / 2) for xy in xys])
                mask = mask.difference(hlist)
        substrate.add(mask)
        return substrate

    def drc(self):
        mask = self.substrate().preview()
        for l in ("GTL", "GBL"):
            lg = self.layers[l].preview()
            if not mask.contains(lg):
                print("Layer", l, "boundary error")
                # self.layers["GTO"].add(lg.difference(mask).buffer(.1))

    def save(self, basename, with_povray=False):
        # self.drc()
        # self.check()
        for (id, l) in self.layers.items():
            with open(basename + "." + id, "wt") as f:
                l.save(f)
        with open(basename + "_PTH.DRL", "wt") as f:
            excellon(f, self.holes, "Plated,1,4,PTH")
        with open(basename + "_NPTH.DRL", "wt") as f:
            excellon(f, self.npth, "NonPlated,1,4,NPTH")

        if with_povray:
            substrate = self.substrate()
            mask = substrate.preview()
            with open(basename + ".sub.pov", "wt") as f:
                substrate.povray(f, "prism { linear_sweep linear_spline 0 1")
            with open(basename + ".gto.pov", "wt") as f:
                self.layers["GTO"].povray(f, mask=mask)
            with open(basename + ".gtl.pov", "wt") as f:
                self.layers["GTL"].povray(f, mask=mask)
            with open(basename + ".gts.pov", "wt") as f:
                self.layers["GTS"].povray(f, mask=mask, invert=True)

        self.bom(basename)
        self.pnp(basename)

    def pnp(self, fn):
        with open(fn + "-pnp.csv", "wt") as f:
            cs = csv.writer(f)
            cs.writerow(
                ["Designator", "Center(X)", "Center(Y)", "Rotatation", "Layer", "Note"]
            )

            def flt(x):
                return "{:.3f}".format(x)

            for f, pp in self.parts.items():
                for p in pp:
                    if p.inBOM:
                        c = p.center
                        (x, y) = c.xy
                        note = p.footprint + "-" + p.mfr + p.val
                        cs.writerow(
                            [p.id, flt(x), flt(y), str(int(c.dir)), "Top", note]
                        )

    def bom(self, fn):
        parts = defaultdict(list)
        rank = "UJKTRCMY"
        for f, pp in self.parts.items():
            for p in pp:
                if p.inBOM:
                    if len(p.source) > 0:
                        vendor = list(p.source.keys())[0]
                        vendor_c = p.source[vendor]
                    else:
                        (vendor, vendor_c) = ("", "")
                    attr = (rank.index(f), p.mfr + p.val, p.footprint, vendor, vendor_c)
                    parts[attr].append(p.id)

        with open(fn + "-bom.csv", "wt") as f:
            c = csv.writer(f)
            c.writerow(["parts", "qty", "device", "package", "vendor", "code"])
            for attr in sorted(parts):
                (f, mfr, footprint, vendor, vendor_c) = attr
                pp = parts[attr]
                c.writerow(
                    [pretty_parts(pp), str(len(pp)), mfr, footprint, vendor, vendor_c]
                )

    def postscript(self, fn, layers=["GTL", "GTO"]):
        ps = ["%!PS-Adobe-2.0"]
        ps.append("72 72 translate")
        ps.append(".05 setlinewidth")

        body = self.body()
        pts = 72 / inches(1)

        def addring(r, style="stroke"):
            ps.append("newpath")
            a = "moveto"
            for (x, y) in r.coords:
                ps.append("%f %f %s" % (x * pts, y * pts, a))
                a = "lineto"
            ps.append(style)

        addring(body.exterior)
        [addring(p) for p in body.interiors]
        for layer in layers:
            for _, p in self.layers[layer].polys:
                if isinstance(p, sg.MultiPolygon):
                    pass
                else:
                    addring(p.exterior)
        # [addring(p.exterior) for (_, p) in self.layers["GTL"].polys]
        rings = [body.exterior] + [r for r in body.interiors]

        ps.append("showpage")

        with open(fn, "wt") as f:
            f.write("".join([l + "\n" for l in ps]))

    def river1(self, i):
        return River(self, [i])

    def enriver(self, ibank, a):
        if a > 0:
            bank = ibank[::-1]
        else:
            bank = ibank
        bank[0].right(a)
        for i, t in enumerate(bank[1:], 1):
            gap = (self.trace + self.space) * i
            t.left(a)
            t.approach(gap, bank[0])
            t.right(2 * a)
        extend(bank[-1], bank)
        return River(self, ibank)

    def enriver90(self, ibank, a):
        if a < 0:
            bank = ibank[::-1]
        else:
            bank = ibank
        bank[0].right(a)
        for i, t in enumerate(bank[1:], 1):
            gap = (self.trace + self.space) * i
            t.forward(gap)
            t.right(a)
        extend(bank[0], bank)
        return River(self, ibank)

    def enriverS(self, pi, a):
        rv = self.enriver(pi, a)
        rv.left(a).wire()
        return rv

    def enriverPair(self, z):
        c = self.trace + self.space
        y = 0.5 * (z[0].distance(z[1]) - c)
        h = math.sqrt(2 * (y ** 2))

        z[0].w("o f .2 l 45 f {0} r 45 f .1".format(h))
        z[1].w("o f .2 r 45 f {0} l 45 f .1".format(h))
        assert (abs(c - z[0].distance(z[1]))) < 1e-3
        return River(self, z)

    def assign(self, part):
        pl = self.parts[part.family]
        pl.append(part)
        return part.family + str(len(pl))

    def logo(self, cx, cy, im, scale=None):
        im = im.convert("L")
        if scale is not None:
            w = int(im.size[0] * scale)
            h = int(im.size[1] * scale)
            im = im.resize((w, h), Image.BICUBIC)
        im = im.point(lambda p: p > 127 and 255)
        (w, h) = im.size
        ar = im.load()
        g = []
        s = 0.04
        ov = 1
        for y in range(h):
            (y0, y1) = (y * s, (y + ov) * s)
            slice = im.crop((0, (h - 1 - y), w, (h - 1 - y) + 1)).tobytes()
            x = 0
            while 255 in slice:
                assert len(slice) == (w - x)
                if slice[0] == 0:
                    l = slice.index(255)
                else:
                    if 0 in slice:
                        l = slice.index(0)
                    else:
                        l = len(slice)
                    g.append(sg.box(x * s, y0, (x + l * ov) * s, y1))
                slice = slice[l:]
                x += l
        g = sa.translate(so.unary_union(g), cx - 0.5 * w * s, cy - 0.5 * h * s).buffer(
            0.001
        )
        self.layers["GTO"].add(g)

    def check(self):
        def npoly(g):
            if isinstance(g, sg.Polygon):
                return 1
            else:
                return len(g)

        g = self.layers["GTL"].preview()

        def clearance(g):
            p0 = micron(0)
            p1 = micron(256)
            while (p1 - p0) > micron(0.25):
                p = (p0 + p1) / 2
                if npoly(g) == npoly(g.buffer(p)):
                    p0 = p
                else:
                    p1 = p
            return 2 * p0

        for l in ("GTL", "GBL"):
            if self.layers[l].polys:
                clr = clearance(self.layers[l].preview())
                if clr < (self.space - micron(1.5)):
                    print(
                        "space violation on layer %s, actual %.3f expected %.3f mm"
                        % (l, clr, self.space)
                    )

        def h2pt(d, xys):
            return so.unary_union([sg.Point(xy).buffer(d / 2) for xy in xys])

        ghole = so.unary_union([h2pt(d, xys) for (d, xys) in self.holes.items()])
        return
        hot_vcc = ghole.intersection(self.layers["GL3"].powered)
        hot_gnd = ghole.intersection(self.layers["GL2"].powered)

        show = [po for po in self.layers["GTL"].p if po.intersects(hot_vcc)]

        # self.layers['GTP'].p = so.unary_union(show)


def extend(dst, traces):
    # extend parallel traces so that they are all level with dst
    assert len({t.dir for t in traces}) == 1, "All traces must be parallel"

    finish_line = dst.copy()
    finish_line.left(90)
    for t in traces:
        t.approach(0, finish_line)


def extend2(traces):
    by_y = {p.seek(traces[0])[1]: p for p in traces}
    extend(by_y[min(by_y)], traces)
