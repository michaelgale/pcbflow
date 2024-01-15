#! /usr/bin/env python3
#
# Turtle style drawing classes

import math

import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from pcbflow import *

SINGLE_TOKENS = ["i", "o"]
PARAM_TOKENS = ["f", "r", "l", ".", ">"]


def token_splitter(tokens):
    """Splits a list of tokens safely so that command tokens are always whitespace
    separated from associated parameter values. e.g. "R90" is equivalent to "R 90"
    """
    exp_tokens = []
    tokens = tokens.split()
    for t in tokens:
        if len(t) > 1 and t[0].lower() in PARAM_TOKENS:
            token = t[0].lower()
            other = t[1:]
            exp_tokens.append(token)
            exp_tokens.append(other)
        else:
            exp_tokens.append(t)
    return exp_tokens


class Turtle:
    """Turtle graphics command parser base class"""

    def __repr__(self):
        return "<at (%.3f, %.3f) facing %.3f>" % (self.xy + (self.dir,))

    def w(self, s, layer="GTL"):
        return self.turtle(s, layer=layer)

    def turtle(self, s, layer="GTL"):
        tokens = token_splitter(s)
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t == "i":
                self.inside()
            elif t == "o":
                self.outside()
            elif t == "f":
                self.forward(float(tokens[i + 1]))
            elif t == "l":
                self.left(float(tokens[i + 1]))
            elif t == "r":
                self.right(float(tokens[i + 1]))
            elif t == ".":
                self.wire()
                self.via_to(tokens[i + 1].upper())
            elif t == ">":
                self.meet_at(tokens[i + 1])

            if t in SINGLE_TOKENS:
                i += 1
            else:
                i += 2
        return self

    def inside(self):
        pass

    def outside(self):
        pass

    def through(self):
        pass


class Draw(Turtle):
    """Drawing context class"""

    def __init__(self, board, xy, dir=0, name=None):
        self.board = board
        self.xy = xy
        self.dir = dir
        self.stack = []
        self.part = None
        self.name = None
        self.newpath()
        self.width = board.drc.trace_width
        self.pw = None
        self.h = None
        self.length = 0
        self.side = "top"
        self.layer = "GTL"

    def is_bottom_layer(self):
        if self.layer in ["GBS", "GBO", "GBL", "GBP", "GBD"]:
            return True
        if self.side == "bottom":
            return True
        return False

    def set_name(self, name):
        self.name = name
        return self

    def set_width(self, width):
        self.width = width
        return self

    def set_layer(self, layer):
        self.layer = layer
        return self

    def newpath(self):
        self.path = [self.xy]
        return self

    def push(self):
        self.stack.append((self.xy, self.dir, self.width))
        return self

    def pop(self):
        (self.xy, self.dir, self.width) = self.stack.pop(-1)
        return self

    def copy(self):
        r = type(self)(self.board, self.xy, self.dir)
        r.h = self.h
        r.layer = self.layer
        r.name = self.name
        r.part = self.part
        r.width = self.width
        r.pw = self.pw
        r.side = self.side
        return r

    def forward(self, d):
        (x, y) = self.xy
        a = (self.dir / 360) * (2 * math.pi)
        (xd, yd) = (d * math.sin(a), d * math.cos(a))
        self.xy = (x + xd, y + yd)
        self.path.append(self.xy)
        return self

    def left(self, d):
        if self.is_bottom_layer():
            self.dir = (self.dir + d) % 360
        else:
            self.dir = (self.dir - d) % 360
        return self

    def right(self, d):
        if self.is_bottom_layer():
            self.dir = (self.dir - d) % 360
        else:
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
        if self.is_bottom_layer():
            self.forward(-x)
        else:
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
        self.pw = w
        self.h = h  # used by inside, outside for pad escape
        return self

    def n_agon(self, radius, sides):
        # an n-agon approximating a circle radius r
        ea = 360 / sides
        self.push()
        half_angle = math.pi / sides
        half_edge = radius * math.tan(half_angle)
        self.forward(radius)
        self.right(90)

        self.newpath()
        for _ in range(sides):
            self.forward(half_edge)
            self.right(ea)
            self.forward(half_edge)
        self.pop()
        self.pw = 2 * radius
        self.h = 2 * radius

    def thermal(self, length, spokes=4):
        for i in range(spokes):
            self.forward(length)
            self.right(180)
            self.forward(length)
            self.right(90)
        return self

    def inside(self):
        mb = self.board.get_part(self.part).bounds
        dleft = abs((self.xy[0] + self.pw / 2) - mb[0])
        dright = abs((self.xy[0] - self.pw / 2) - mb[2])
        dtop = abs((self.xy[1] - self.h / 2) - mb[3])
        dbottom = abs((self.xy[1] + self.h / 2) - mb[1])
        min_diff = min([dleft, dright, dtop, dbottom])
        if min_diff == dleft:
            self.dir = 90
            self.xy = (self.xy[0] + self.pw / 2, self.xy[1])
        elif min_diff == dright:
            self.dir = -90
            self.xy = (self.xy[0] - self.pw / 2, self.xy[1])
        elif min_diff == dtop:
            self.dir = 180
            self.xy = (self.xy[0], self.xy[1] - self.h / 2)
        elif min_diff == dbottom:
            self.dir = 0
            self.xy = (self.xy[0], self.xy[1] + self.h / 2)
        else:
            self.right(180)
            ml = max(self.pw, self.h) / 2
            self.forward(ml)
        return self

    def outside(self):
        mb = self.board.get_part(self.part).bounds
        dleft = abs((self.xy[0] - self.pw / 2) - mb[0])
        dright = abs((self.xy[0] + self.pw / 2) - mb[2])
        dtop = abs((self.xy[1] + self.h / 2) - mb[3])
        dbottom = abs((self.xy[1] - self.h / 2) - mb[1])
        min_diff = min([dleft, dright, dtop, dbottom])
        if min_diff == dleft:
            self.dir = -90
            self.xy = (self.xy[0] - self.pw / 2, self.xy[1])
        elif min_diff == dright:
            self.dir = 90
            self.xy = (self.xy[0] + self.pw / 2, self.xy[1])
        elif min_diff == dtop:
            self.dir = 0
            self.xy = (self.xy[0], self.xy[1] + self.h / 2)
        elif min_diff == dbottom:
            self.dir = 180
            self.xy = (self.xy[0], self.xy[1] - self.h / 2)
        else:
            ml = max(self.pw, self.h) / 2
            self.forward(ml)
        return self

    def square(self, width):
        return self.rect(width, width)

    def poly(self):
        return sg.Polygon(self.path)

    def smd_pad(self, layer=None, no_mask=False):
        if layer is not None:
            self.layer = layer
        g = self.poly()
        if self.layer == "GTL":
            layers = self.board.get_smd_pad_layers(side="top")
            if no_mask:
                layers = [self.board.layers["GTL"]]
        elif self.layer == "GBL":
            layers = self.board.get_smd_pad_layers(side="bottom")
            if no_mask:
                layers = [self.board.layers["GBL"]]
        else:
            assert False, "Attempt to create pad in layer " + self.layer
        for lyr in layers:
            lyr.add(g, self.name)

    def pin_pad(self):
        for layer in self.board.get_pad_stack_layers():
            if layer.is_mask:
                g = sg.Polygon(self.path).buffer(self.board.drc.soldermask_margin)
            else:
                g = sg.Polygon(self.path)
            layer.add(g, self.name)

    def silk(self, side="top"):
        g = sg.LineString(self.path).buffer(self.board.drc.silk_width / 2)
        self.board.get_silk_layer(side).add(g)

    def outline(self):
        g = sg.LinearRing(self.path)
        self.board.layers["GML"].add(g)

    def drill(self, d):
        self.board.add_drill(self.xy, d)

    def via_to(self, next_layer):
        self.via(connect=self.name)
        self.layer = next_layer

    def via(self, connect=None):
        dv = self.board.drc.via_drill / 2 + self.board.drc.via_annular_ring
        g = sg.Point(self.xy).buffer(dv)
        for layer in self.board.get_copper_layers():
            layer.add(g, connect)
        if connect is not None:
            self.board.layers[self.layer].connected.append(g)
        self.board.add_drill(self.xy, self.board.drc.via_drill)
        if self.board.drc.mask_vias:
            gm = sg.Point(self.xy).buffer(dv + self.board.drc.soldermask_margin)
            self.board.add_to_mask_layers(gm)
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

    def wvia(self, layer, net=None, length=None):
        tl = self.board.drc.clearance + self.board.drc.via_drill
        if length is not None:
            tl = length
        self.forward(tl)
        self.wire(width=self.board.drc.via_track_width, layer=layer)
        self.via(net)

    def fan(self, l, dst):
        for a in (-45, 0, 45):
            self.copy().right(a).forward(l).wire(width=0.8).via(dst)

    def platedslot(self, buf):
        brd = self.board
        g1 = sg.LineString(self.path).buffer(buf)
        g2 = sg.LinearRing(g1.exterior.coords)
        brd.layers["GML"].add(g2)
        g3 = g1.buffer(
            self.board.drc.soldermask_margin + self.board.drc.via_annular_ring
        )
        self.board.add_to_mask_layers(g3)
        g3 = g1.buffer(self.board.drc.via_annular_ring)
        g4 = g3.difference(g1.buffer(-self.board.drc.via_annular_ring / 2))
        for l in self.board.get_copper_layers(as_names=True):
            brd.layers[l].add(g4)
        strut_x = sa.scale(g4.envelope, yfact=0)
        strut_y = sa.scale(g4.envelope, xfact=0)
        struts = strut_x.union(strut_y)
        brd.get_paste_layer(self.side).add(g4.difference(struts))

    def meet(self, other):
        self.path.append(other.xy)
        return self.wire()

    def meet_at(self, other):
        dest = other.split("-")
        ref, pad = dest[0], int(dest[1])
        part = self.board.get_part(ref)
        if part is not None:
            loc = part.pads[pad].xy
            # (dx, dy) = self.seek(part.pads[pad])
            self.path.append(loc)
            return self.wire()
        return self

    def _text(self, s, side, justify="centre"):
        (x, y) = self.xy
        layer = self.board.get_silk_layer(side)
        linewidth = self.board.drc.text_silk_width
        if justify == "left":
            layer.add(hershey.ltext(x, y, s, side=side, linewidth=linewidth))
        else:
            layer.add(hershey.ctext(x, y, s, side=side, linewidth=linewidth))
        return self

    def text(self, s, side="top"):
        return self._text(s, side, justify="centre")

    def ltext(self, s, side="top"):
        return self._text(s, side, justify="left")

    def through(self):
        self.wire()
        dst = {"GTL": "GBL", "GBL": "GTL"}[self.layer]
        self.via().set_layer(dst)
        return self
