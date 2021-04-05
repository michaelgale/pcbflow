#! /usr/bin/env python3
#
# Top level Board class
#


from collections import defaultdict
import os
import re
import math
import csv

from PIL import Image
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so
import math

from pcbflow import *


class Board:
    def __init__(self, size):
        self.size = size
        self.drc = DRC()
        self.parts = defaultdict(list)
        self.holes = defaultdict(list)
        self.npth = defaultdict(list)
        self.keepouts = []

        self.counters = defaultdict(lambda: 0)
        self.nets = []

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

    def parts_str(self):
        s = []
        for k, v in self.parts.items():
            for p in v:
                s.append(str(p))
        return "\n".join(s)

    def layer_net_str(self):
        s = []
        for k, v in self.layers.items():
            if isinstance(v, Layer):
                ld = defaultdict(int)
                sd = []
                for net in v.polys:
                    if net[0] is not None:
                        ld[net[0]] += 1
                for kd, vd in ld.items():
                    sd.append("%s: %d " % (kd, vd))
                if len(sd) > 0:
                    s.append("Layer %s [%-20s] nets: %s" % (k, v.desc, "".join(sd)))
        return "\n".join(s)

    def boundary(self, r=0):
        x0, y0 = (-r, -r)
        x1, y1 = self.size
        x1 += r
        y1 += r
        return sg.LinearRing([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def boundary_keepout(self):
        x0, y0 = (0, 0)
        x1, y1 = self.size
        bo = sg.LinearRing([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]).buffer(
            self.drc.outline_clearance
        )
        self.keepouts.append(bo)

    def outline(self):
        self.layers["GML"].add(self.boundary())
        self.boundary_keepout()

    def oversize(self, r):
        self.layers["GML"].add(self.boundary(r))
        sr = self.drc.silk_width / 2
        g = self.boundary(1.1 * sr).buffer(sr)
        self.layers["GTO"].add(g.buffer(0))

    def add_hole(self, xy, diameter):
        self.npth[diameter].append(xy)
        self.keepouts.append(
            sg.Point(xy).buffer(diameter / 2 + self.drc.hole_clearance)
        )
        gm = sg.Point(xy).buffer(diameter / 2 + self.drc.hole_mask)
        if self.drc.mask_holes:
            self.layers["GTS"].add(gm)
            self.layers["GBS"].add(gm)

    def add_drill(self, xy, diameter):
        self.holes[diameter].append(xy)

    def add_keepout_to_obj(self, obj, layer=None):
        bb = obj.bounds
        g = sg.box(bb[0], bb[1], bb[2], bb[3]).buffer(self.drc.clearance)
        if layer is not None:
            self.layers[layer].keepouts.append(g)
        else:
            self.keepouts.append(g)

    def add_mask_to_obj(self, obj, side="top"):
        bb = obj.bounds
        g = sg.box(bb[0], bb[1], bb[2], bb[3]).buffer(self.drc.soldermask_margin)
        if side == "top":
            self.layers["GTS"].add(g)
        else:
            self.layers["GBS"].add(g)

    def add_text(
        self,
        xy,
        text,
        scale=1.0,
        side="top",
        layer="GTO",
        keepout_box=False,
        soldermask_box=False,
    ):
        (x, y) = xy
        gt = hershey.text(
            x, y, text, scale=scale, side=side, linewidth=self.drc.text_silk_width
        )
        self.layers[layer].add(gt)
        if keepout_box:
            self.add_keepout_to_obj(gt, layer=layer)
        if soldermask_box:
            self.add_mask_to_obj(gt, side)

    def add_bitmap(
        self,
        xy,
        fn,
        scale=None,
        side="top",
        layer=None,
        keepout_box=False,
        soldermask_box=False,
    ):
        (x, y) = xy
        im = Image.open(fn)
        im = im.convert("L")
        if side.lower() == "bottom":
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if scale is not None:
            w = int(im.size[0] * scale)
            h = int(im.size[1] * scale)
            im = im.resize((w, h), Image.BICUBIC)
        im = im.point(lambda p: p > 127 and 255)
        (w, h) = im.size
        ar = im.load()
        g = []
        s = self.drc.bitmap_res
        ov = 1
        for yh in range(h):
            (y0, y1) = (yh * s, (yh + ov) * s)
            slice = im.crop((0, (h - 1 - yh), w, (h - 1 - yh) + 1)).tobytes()
            xb = 0
            while 255 in slice:
                assert len(slice) == (w - xb)
                if slice[0] == 0:
                    l = slice.index(255)
                else:
                    if 0 in slice:
                        l = slice.index(0)
                    else:
                        l = len(slice)
                    g.append(sg.box(xb * s, y0, (xb + l * ov) * s, y1))
                slice = slice[l:]
                xb += l
        g = sa.translate(so.unary_union(g), x - 0.5 * w * s, y - 0.5 * h * s).buffer(
            0.001
        )
        lyr = layer
        if side.lower() == "top":
            lyr = "GTO" if layer is None else layer
            self.layers[lyr].add(g)
        else:
            lyr = "GBO" if layer is None else layer
            self.layers[lyr].add(g)
        if keepout_box:
            self.add_keepout_to_obj(g, layer=lyr)
        if soldermask_box:
            self.add_mask_to_obj(g, side)

    def DC(self, xy, d=0):
        return Draw(self, xy, d)

    def DCf(self, xy, d=0):
        return Drawf(self, xy, d)

    def fill_layer(self, layer, netname):
        la = self.layers[layer]
        kol = so.unary_union(la.keepouts)
        ko = kol.union(so.unary_union(self.keepouts))
        g = self.body().buffer(-self.drc.clearance).difference(ko)
        notouch = so.unary_union([o for (nm, o) in la.polys if nm != netname])
        self.layers[layer].add(
            g.difference(notouch.buffer(self.drc.clearance)), netname
        )

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

    def perform_drc(self):
        mask = self.substrate().preview()
        for l in ("GTL", "GBL"):
            lg = self.layers[l].preview()
            if not mask.contains(lg):
                print("Layer", l, "boundary error")

    def save(self, basename, in_subdir=True, with_povray=False):
        if in_subdir:
            newpath = os.path.normpath("./%s" % (basename))
            if not os.path.isdir(newpath):
                try:
                    os.mkdir(newpath)
                except OSError:
                    print("Directory %s cannot be created" % (newpath))
            assetpath = os.path.normpath("./%s" % (basename) + os.sep + basename)
        else:
            assetpath = basename
        for (id, l) in self.layers.items():
            with open(assetpath + "." + id, "wt") as f:
                l.save(f)
        with open(assetpath + "_PTH.DRL", "wt") as f:
            excellon(f, self.holes, "Plated,1,4,PTH")
        with open(assetpath + "_NPTH.DRL", "wt") as f:
            excellon(f, self.npth, "NonPlated,1,4,NPTH")

        if with_povray:
            substrate = self.substrate()
            mask = substrate.preview()
            with open(assetpath + ".sub.pov", "wt") as f:
                substrate.povray(f, "prism { linear_sweep linear_spline 0 1")
            with open(assetpath + ".gto.pov", "wt") as f:
                self.layers["GTO"].povray(f, mask=mask)
            with open(assetpath + ".gtl.pov", "wt") as f:
                self.layers["GTL"].povray(f, mask=mask)
            with open(assetpath + ".gts.pov", "wt") as f:
                self.layers["GTS"].povray(f, mask=mask, invert=True)

        self.bom(assetpath)
        self.pnp(assetpath)

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
                        note = p.footprint
                        if len(p.mfr) > 0:
                            note += "-" + p.mfr
                        if len(p.val) > 0:
                            note += "-" + p.val
                        cs.writerow(
                            [p.id, flt(x), flt(y), str(int(c.dir)), p.side, note]
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
        pts = 72 / INCHES(1)

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
        return Route(self, [i])

    def enriver(self, ibank, a):
        if a > 0:
            bank = ibank[::-1]
        else:
            bank = ibank
        bank[0].right(a)
        for i, t in enumerate(bank[1:], 1):
            gap = self.drc.channel() * i
            t.left(a)
            t.approach(gap, bank[0])
            t.right(2 * a)
        extend(bank[-1], bank)
        return Route(self, ibank)

    def enriver90(self, ibank, a):
        if a < 0:
            bank = ibank[::-1]
        else:
            bank = ibank
        bank[0].right(a)
        for i, t in enumerate(bank[1:], 1):
            gap = self.drc.channel() * i
            t.forward(gap)
            t.right(a)
        extend(bank[0], bank)
        return Route(self, ibank)

    def enriverS(self, pi, a):
        rv = self.enriver(pi, a)
        rv.left(a).wire()
        return rv

    def enriverPair(self, z):
        c = self.drc.channel()
        y = 0.5 * (z[0].distance(z[1]) - c)
        h = math.sqrt(2 * (y ** 2))

        z[0].w("o f .2 l 45 f {0} r 45 f .1".format(h))
        z[1].w("o f .2 r 45 f {0} l 45 f .1".format(h))
        assert (abs(c - z[0].distance(z[1]))) < 1e-3
        return Route(self, z)

    def assign(self, part):
        pl = self.parts[part.family]
        pl.append(part)
        return part.family + str(len(pl))

    def check(self):
        def npoly(g):
            if isinstance(g, sg.Polygon):
                return 1
            else:
                return len(g)

        g = self.layers["GTL"].preview()

        def clearance(g):
            p0 = MICRONS(0)
            p1 = MICRONS(256)
            while (p1 - p0) > MICRONS(0.25):
                p = (p0 + p1) / 2
                if npoly(g) == npoly(g.buffer(p)):
                    p0 = p
                else:
                    p1 = p
            return 2 * p0

        for l in ("GTL", "GBL"):
            if self.layers[l].polys:
                clr = clearance(self.layers[l].preview())
                if clr < (self.space - MICRONS(1.5)):
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
