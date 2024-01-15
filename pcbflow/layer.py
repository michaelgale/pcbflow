#! /usr/bin/env python3
#
# Layer classes

from collections import defaultdict

import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from pcbflow import *

DEFAULT_LAYER_ORDER = [
    "GTD",
    "GML",
    "GTP",
    "GTO",
    "GTS",
    "GTL",
    "GP2",
    "GP3",
    "GP4",
    "GP5",
    "GP6",
    "GP7",
    "GP8",
    "GBL",
    "GBS",
    "GBO",
    "GBP",
    "GBD",
]

DEFAULT_LAYERS = {
    "GTD": {
        "desc": "Top Documentation",
        "function": "AssemblyDrawing,Top",
        "is_document": True,
        "z_order": 0,
    },
    "GTP": {
        "desc": "Top Paste",
        "function": "Paste,Top",
        "is_paste": True,
        "z_order": 1,
    },
    "GTO": {
        "desc": "Top Silkscreen",
        "function": "Legend,Top",
        "is_silk": True,
        "z_order": 2,
    },
    "GTS": {
        "desc": "Top Solder Mask",
        "function": "Soldermask,Top",
        "is_mask": True,
        "z_order": 3,
    },
    "GTL": {
        "desc": "Top Copper",
        "function": "Copper,L1,Top",
        "is_copper": True,
        "z_order": 4,
    },
    "GBL": {
        "desc": "Bottom Copper",
        "function": "Copper,L2,Bot",
        "is_copper": True,
        "z_order": 5,
    },
    "GBS": {
        "desc": "Bottom Solder Mask",
        "function": "Soldermask,Bot",
        "is_mask": True,
        "z_order": 6,
    },
    "GBO": {
        "desc": "Bottom Silkscreen",
        "function": "Legend,Bot",
        "is_silk": True,
        "z_order": 7,
    },
    "GBP": {
        "desc": "Bottom Paste",
        "function": "Paste,Bot",
        "is_paste": True,
        "z_order": 8,
    },
    "GBD": {
        "desc": "Bottom Documentation",
        "function": "AssemblyDrawing,Bot",
        "is_document": True,
        "z_order": 9,
    },
}


class Layer:
    def __init__(self, board=None, **kwargs):
        self.polys = []
        self.named_polys = []
        self.fill_poly = None
        self.desc = ""
        self.function = ""
        self.enabled = True
        self.z_order = 0
        self.is_silk = False
        self.is_copper = False
        self.is_mask = False
        self.is_paste = False
        self.is_inner = False
        self.is_outline = False
        self.is_document = False
        self.connected = []
        self.keepouts = []
        self.preview_poly = None
        self.board = board
        if "drc" not in kwargs:
            self.drc = DRC()
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def __str__(self):
        return (
            "%-16s Order: %d Inner: %-5s Cu: %-5s Mask: %-5s Paste: %-5s Silk: %-5s Outline: %-5s Docu: %-5s"
            % (
                self.function,
                self.z_order,
                self.is_inner,
                self.is_copper,
                self.is_mask,
                self.is_paste,
                self.is_silk,
                self.is_outline,
                self.is_document,
            )
        )

    def add(self, obj, name=None):
        self.polys.append((name, obj.simplify(0.001, preserve_topology=False)))
        self.preview_poly = None

    def add_named(self, obj, name):
        self.named_polys.append((name, obj.simplify(0.001, preserve_topology=False)))
        self.preview_poly = None

    def preview(self, as_collection=False):
        if self.preview_poly is None:
            named_polys = [p for (_, p) in self.named_polys]
            all_polys = [p for (_, p) in self.polys]
            name_dict = defaultdict(int)
            for netname, _ in self.named_polys:
                if netname is not None:
                    name_dict[netname] += 1
            exclusions = []
            for netname in name_dict:
                exc = so.unary_union([o for (name, o) in self.polys if name != netname])
                exclusions.append(exc.simplify(0.001, preserve_topology=False))
            if len(exclusions) > 0:
                diff_exc = so.unary_union([p for p in exclusions]).buffer(
                    self.drc.clearance
                )
                ncp = so.unary_union(named_polys).difference(diff_exc)
                if self.board is not None:
                    ko = so.unary_union([*self.keepouts, *self.board.keepouts])
                    ncp = ncp.difference(ko)
                self.preview_poly = so.unary_union([*all_polys, ncp])
            else:
                self.preview_poly = so.unary_union([*all_polys, *named_polys])
        if self.fill_poly is not None:
            self.preview_poly = so.unary_union([self.preview_poly, self.fill_poly])
        if isinstance(self.preview_poly, sg.Polygon):
            return self.preview_poly
        if as_collection:
            return self.preview_poly
        return self.preview_poly.geoms

    def paint(self, bg, include, clearance):
        # Return the intersection of bg with the current polylist
        # touching the included, avoiding the others by distance r
        ingrp = so.unary_union([bg] + [o for (nm, o) in self.polys if nm == include])
        exgrp = so.unary_union([o for (nm, o) in self.polys if nm != include])
        self.powered = so.unary_union(ingrp).difference(exgrp.buffer(clearance))
        return exgrp.union(self.powered)

    def fill(self, bg, include, clearance):
        self.polys = [("filled", self.paint(bg, include, clearance))]

    def save(self, f):
        surface = self.preview()
        g = Gerber(f, self.desc)
        g.file_function(self.function)

        def renderpoly(g, po):
            if type(po) == sg.MultiPolygon:
                [renderpoly(g, p) for p in po.geoms]
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
                [renderpoly(p) for p in po.geoms]
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


class OutlineLayer(Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lines = []
        self.is_outline = True

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
