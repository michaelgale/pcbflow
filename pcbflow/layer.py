#! /usr/bin/env python3
#
# Layer classes


import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from pcbflow import *



class Layer:
    def __init__(self, desc, function):
        self.polys = []
        self.desc = desc
        self.function = function
        self.connected = []
        self.p = None
        self.keepouts = []

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
                eps = 0.0
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
