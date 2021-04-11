#! /usr/bin/env python3
#
# Eagle library part importer
#

import os, sys
import math
from collections import defaultdict

import xml.etree.ElementTree as ET
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from .part import PCBPart
from .util import col_print, infer_family

LAYER_DIMENSION = "20"
LAYER_TPLACE = "21"
LAYER_TDOCU = "51"
DOC_LAYERS = (LAYER_DIMENSION, LAYER_TPLACE, LAYER_TDOCU)


def list_lbr_packages(fn):
    tree = ET.parse(fn)
    root = tree.getroot()
    x_packages = root.find("drawing").find("library").find("packages")
    packages = sorted([p.attrib["name"] for p in x_packages])
    col = 0
    s = []
    col_print(packages)
    return len(packages)


def show_lbr_package(fn, package):
    tree = ET.parse(fn)
    root = tree.getroot()
    x_packages = root.find("drawing").find("library").find("packages")
    packages = {p.attrib["name"]: p for p in x_packages}
    for k, v in packages.items():
        if k == package:
            conn = {}
            d = defaultdict(int)
            for va in v:
                d[va.tag] += 1
                if va.tag in ("pad", "smd"):
                    conn[va.attrib["name"]] = (
                        float(va.attrib["x"]),
                        float(va.attrib["y"]),
                    )
            print("Package %s in %s : " % (package, fn))
            s = []
            for ka, va in d.items():
                s.append("  %s: %d," % (ka, va))
            s = "".join(s).rstrip(",")
            print("  Entities: %s" % (s))
            s = []
            for ka, va in conn.items():
                s.append("  %3s: %s" % (ka, va))
            print("  Pads:")
            col_print(s)


def parse_rotation(attr):
    if "rot" in attr:
        rs = attr["rot"].replace("R", "").replace("S", "")
        try:
            rot = float(rs)
            return rot
        except:
            return 0.0
    return 0.0


class EaglePart(PCBPart):
    def __init__(
        self,
        dc,
        val=None,
        source=None,
        libraryfile=None,
        partname=None,
        debug=False,
        **kwargs
    ):
        self.debug = debug
        self.libraryfile = libraryfile
        self.partname = partname
        self.use_silk = True
        tree = ET.parse(self.libraryfile)
        root = tree.getroot()
        x_packages = root.find("drawing").find("library").find("packages")
        packages = {p.attrib["name"]: p for p in x_packages}
        if self.partname not in packages:
            raise ValueError("Part not found in library")
        self.pa = packages[self.partname]
        self.footprint = self.partname
        self.family = infer_family(self.partname)
        super().__init__(dc, val, source, **kwargs)
        self.labels = {}
        self.terminals = {}

    def _print_attr(self, label, attr):
        s = []
        s.append("%s : " % (label))
        for k, v in attr.items():
            s.append("%s: %s, " % (k, v))
        print("".join(s).rstrip(","))

    def place(self, dc):
        ls = defaultdict(list)
        attr = {}
        self.labels = {}
        for c in self.pa:
            attr = c.attrib
            if c.tag == "text" and attr["layer"] in DOC_LAYERS:
                if self.debug:
                    self._print_attr(c.tag, attr)
                (x, y, size) = [float(attr[t]) for t in "x y size".split()]
                rot = parse_rotation(attr)
                p = dc.copy().goxy(x, y)
                self.labels[c.text] = {"xy": p.xy, "rot": rot, "size": size}

            elif c.tag == "wire" and attr["layer"] in DOC_LAYERS:
                if self.debug:
                    self._print_attr(c.tag, attr)
                (x1, y1, x2, y2) = [float(attr[t]) for t in "x1 y1 x2 y2".split()]
                p0 = dc.copy().goxy(x1, y1)
                p1 = dc.copy().goxy(x2, y2)
                ls[attr["layer"]].append(sg.LineString([p0.xy, p1.xy]))

            elif c.tag == "rectangle" and attr["layer"] in DOC_LAYERS:
                if self.debug:
                    self._print_attr(c.tag, attr)
                rot = parse_rotation(attr)
                (x1, y1, x2, y2) = [float(attr[t]) for t in "x1 y1 x2 y2".split()]
                xl = x2 - x1
                yl = y2 - y1
                r0 = (
                    dc.copy()
                    .goxy(x1 + xl / 2, y1 + yl / 2)
                    .right(rot)
                    .rect(xl, yl)
                    .poly()
                )
                self.board.get_silk_layer(side=self.side).add(r0)

            elif c.tag == "hole":
                if self.debug:
                    self._print_attr(c.tag, attr)
                (x, y, drill) = [float(attr[t]) for t in "x y drill".split()]
                p = dc.copy().goxy(x, y)
                dc.board.add_hole(p.xy, drill)

            elif c.tag == "circle" and attr["layer"] == LAYER_DIMENSION:
                if self.debug:
                    self._print_attr(c.tag, attr)
                (x, y, radius) = [float(attr[t]) for t in "x y radius".split()]
                p = dc.copy().goxy(x, y)
                dc.board.add_drill(p.xy, 2 * radius)

            elif c.tag == "smd":
                if self.debug:
                    self._print_attr(c.tag, attr)
                rot = parse_rotation(attr)
                (x, y, dx, dy) = [float(attr[t]) for t in "x y dx dy".split()]
                p = dc.copy().goxy(x, y).right(rot)
                p.rect(dx, dy)
                p.set_name(attr["name"])
                no_paste = False
                if "cream" in attr:
                    if attr["cream"].lower() == "no":
                        no_paste = True
                self.smd_pad(p, ignore_paste=no_paste)

            elif c.tag == "pad":
                if self.debug:
                    self._print_attr(c.tag, attr)
                (x, y, drill) = [float(attr[t]) for t in "x y drill".split()]
                if "diameter" not in attr:
                    diameter = drill + self.board.drc.via_annular_ring * 2
                else:
                    diameter = float(attr["diameter"])
                rot = parse_rotation(attr)
                nm = attr["name"]
                dc.push()
                dc.goxy(x, y)
                dc.board.add_drill(dc.xy, drill)
                shape = attr.get("shape", "circle")
                if shape in ["long", "circle", "octagon", "square"]:
                    n = {"long": 60, "circle": 60, "octagon": 8, "square": 4}[shape]
                    if shape == "square":
                        diameter /= 1.1
                    attr["shape"] = "circle"
                    p = dc.copy()
                    p.n_agon(diameter / 2, n)
                    p.set_name(nm)
                    p.part = self.id
                    self.pads.append(p)
                    p.pin_pad()
                    dc.pop()

        if ls[LAYER_DIMENSION]:
            g = so.linemerge(ls[LAYER_DIMENSION])
            self.board.layers["GML"].add(g)

        if ls[LAYER_TDOCU]:
            g = so.linemerge(ls[LAYER_TDOCU]).buffer(self.board.drc.silk_width / 2)
            self.board.get_docu_layer(side=self.side).add(g)

        if self.use_silk and ls[LAYER_TPLACE]:
            g = so.linemerge(ls[LAYER_TPLACE]).buffer(self.board.drc.silk_width / 2)
            self.board.get_silk_layer(side=self.side).add(g)

        if len(self.labels) > 0:
            for k, v in self.labels.items():
                self.board.add_text(
                    v["xy"],
                    k,
                    angle=v["rot"],
                    scale=v["size"],
                    side=self.side,
                    justify="left",
                )
