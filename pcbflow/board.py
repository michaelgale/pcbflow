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
    def __init__(self, size=(80, 50)):
        self.size = size
        self.drc = DRC()
        self.parts = defaultdict(list)
        self.holes = defaultdict(list)
        self.npth = defaultdict(list)
        self.keepouts = []
        self.layers = {}

        self.counters = defaultdict(lambda: 0)
        self.nets = []
        self.config_default_layers()

    def DC(self, xy, d=0):
        """Returns a drawing context from the current board.

        :param xy: x, y coordinate tuple
        :param d: d direction angle (deg)

        :returns: :obj:`Draw` drawing context object
        """
        return Draw(self, xy, d)

    def assign(self, part):
        """Assigns a reference designator/id to a part and adds the part to the board.

        :param part : A PCBPart derived object

        :returns: :obj:`str` reference designator assigned to part
        """
        pl = self.parts[part.family]
        pl.append(part)
        return part.family + str(len(pl))

    def addnet(self, a, b):
        self.nets.append(((a.part, a.name), (b.part, b.name)))

    def get_part(self, ref):
        """Returns a PCBPart object reference from a reference designator.

        :param ref : Reference designator string (e.g. "U1")

        :returns: :obj:`PCBPart` reference to PCBPart derived object with matching ref des
        """
        for k, v in self.parts.items():
            for p in v:
                if p.id == ref:
                    return p
        return None

    #########################################################################
    #
    # Layer Methods
    #
    #########################################################################

    def config_default_layers(self):
        """Resets all PCB layers and configures them to a default configuration."""
        self.layers = {}
        for k, v in DEFAULT_LAYERS.items():
            self.layers[k] = Layer(board=self, drc=self.drc, **v)
        self.layers["GML"] = OutlineLayer(desc="Mechanical", function="Profile,NP")
        self.reorder_layer_stack()

    def reorder_layer_stack(self):
        """Reorders the layer stackup ensuring the correct ordering of copper layers."""
        z_order = 0
        cu_order = 1
        for layer in DEFAULT_LAYER_ORDER:
            if layer in self.layers:
                self.layers[layer].z_order = z_order
                if self.layers[layer].is_copper:
                    fn = "Copper,L%d," % (cu_order)
                    if layer == "GTL":
                        desc = "Top Copper"
                        fn += "Top"
                    elif layer == "GBL":
                        desc = "Bottom Copper"
                        fn += "Bot"
                    else:
                        desc = "Inner Copper Layer %d" % (cu_order)
                        fn += "Inr"
                    self.layers[layer].desc = desc
                    self.layers[layer].function = fn
                    cu_order += 1
                z_order += 1

    def get_copper_layers(self, as_names=False):
        """Returns a list of all the copper layers.

        :param as_names: Specifies whether to return the layer list as a list of
        string names or a list of Layer object references.

        :returns: :obj:`list` of string names or Layer objects
        """
        layers = []
        for k in self.layers:
            if self.layers[k].is_copper:
                if as_names:
                    layers.append(k)
                else:
                    layers.append(self.layers[k])
        return layers

    def add_inner_copper_layer(self, layer_count=1):
        """Adds one or more copper layers between the top and bottom copper layers.

        :param layer_count : Specifies how many copper layers to insert
        """
        for _ in range(layer_count):
            cu_layers = self.get_copper_layers()
            n_inner = len(cu_layers)
            new_layer = "GP%d" % (n_inner)
            self.layers[new_layer] = Layer(board=self, is_copper=True, is_inner=True)
            self.reorder_layer_stack()

    def get_smd_pad_layers(self, side="top", as_names=False, ignore_paste=False):
        """Returns a list of layers which make up a pad stack for a surface mount pad.

        :param side: Specifies either the "top" or "bottom" side of the PCB
        :param as_names: Specifies whether to return the layer list as a list of
        string names or a list of Layer object references.
        :param ignore_paste: Specifies whether to ignore the solder paste layer
        from the returned layer list

        :returns: :obj:`list` of string names or Layer objects
        """
        layers = []
        for k, v in self.layers.items():
            if side.title()[:3] in v.function and not v.is_silk and not v.is_document:
                if ignore_paste and v.is_paste:
                    pass
                elif as_names:
                    layers.append(k)
                else:
                    layers.append(self.layers[k])
        return layers

    def get_pad_stack_layers(self, as_names=False):
        """Returns a list of layers which make up a pad stack for a through hole pad.

        :param as_names : Specifies whether to return the layer list as a list of
        string names or a list of Layer object references.

        :returns: :obj:`list` of string names or Layer objects
        """
        layers = []
        layers.extend(self.get_copper_layers(as_names=as_names))
        layers.extend(
            self.get_smd_pad_layers(side="top", as_names=as_names, ignore_paste=True)
        )
        layers.extend(
            self.get_smd_pad_layers(side="bottom", as_names=as_names, ignore_paste=True)
        )
        layers = list(set(layers))
        return layers

    def _get_layer(self, key, side, as_name):
        for k, v in self.layers.items():
            if v.__dict__[key] and side.title()[:3] in v.function:
                if as_name:
                    return k
                return self.layers[k]
        return None

    def get_silk_layer(self, side="top", as_name=False):
        """Returns the silkscreen layer for the desired side of the PCB.

        :param side : Specifies either the "top" or "bottom" side of the PCB
        :param as_name : Specifies whether to return the layer as a
        string name or a Layer object reference

        :returns: either a :obj:`str` name or :obj:`Layer` object reference
        """
        return self._get_layer("is_silk", side, as_name)

    def get_docu_layer(self, side="top", as_name=False):
        """Returns the documentation layer for the desired side of the PCB.

        :param side : Specifies either the "top" or "bottom" side of the PCB
        :param as_name : Specifies whether to return the layer as a
        string name or a Layer object reference

        :returns: either a :obj:`str` name or :obj:`Layer` object reference
        """
        return self._get_layer("is_document", side, as_name)

    def get_paste_layer(self, side="top", as_name=False):
        """Returns the solder paste layer for the desired side of the PCB.

        :param side : Specifies either the "top" or "bottom" side of the PCB
        :param as_name : Specifies whether to return the layer as a
        string name or a Layer object reference

        :returns: either a :obj:`str` name or :obj:`Layer` object reference
        """
        return self._get_layer("is_paste", side, as_name)

    def get_mask_layer(self, side="top", as_name=False):
        """Returns the solder mask layer for the desired side of the PCB.

        :param side : Specifies either the "top" or "bottom" side of the PCB
        :param as_name : Specifies whether to return the layer as a
        string name or a Layer object reference

        :returns: either a :obj:`str` name or :obj:`Layer` object reference
        """
        return self._get_layer("is_mask", side, as_name)

    def fill_layer(self, layer, netname):
        """Fills a layer with copper poured region assigned to a net name.

        :param layer : string name of the layer (e.g. "GTL")
        :param netname : string name of net to assign to the fill
        """
        if layer not in self.layers:
            print("Warning: Cannot fill layer %s; not in layer stack." % (layer))
            return
        lyr = self.layers[layer]
        ko = so.unary_union([*lyr.keepouts, *self.keepouts])
        g = self.body().buffer(-self.drc.clearance).difference(ko)
        ap = [p for (name, p) in lyr.polys if name != netname]
        np = [p for (name, p) in lyr.named_polys if name != netname]
        exclusions = so.unary_union([*ap, *np])
        lyr.fill_poly = g.difference(exclusions.buffer(self.drc.clearance))

    def add_to_mask_layers(self, obj):
        """Adds a polygon object to both the solder mask layers.

        :param obj : Polygon object to add
        """
        self.layers["GTS"].add(obj)
        self.layers["GBS"].add(obj)

    #########################################################################
    #
    # String Methods
    #
    #########################################################################

    def parts_str(self):
        s = []
        for k, v in self.parts.items():
            for p in v:
                s.append(str(p))
        return "\n".join(s)

    def layer_stack_str(self):
        s = []
        for layer in DEFAULT_LAYER_ORDER:
            if layer in self.layers:
                s.append("Layer %s : %s" % (layer, str(self.layers[layer])))
        return "\n".join(s)

    def layer_net_str(self):
        s = []
        for layer in DEFAULT_LAYER_ORDER:
            if layer in self.layers:
                if self.layers[layer].is_copper:
                    ld = defaultdict(int)
                    sd = []
                    for net in self.layers[layer].polys:
                        if net[0] is not None:
                            ld[net[0]] += 1
                    for kd, vd in ld.items():
                        sd.append("%s: %d " % (kd, vd))
                    if len(sd) > 0:
                        s.append(
                            "Layer %s : %-16s Nets: %d"
                            % (layer, self.layers[layer].function, len(sd))
                        )
                        s.append(col_str(sd))
        return "\n".join(s)

    #########################################################################
    #
    # Add PCB Object Methods
    #
    #########################################################################

    def add_outline(self):
        self.layers["GML"].add(self.boundary())
        self.boundary_keepout()

    def add_named_rect(self, top_left, bottom_right, layer, name):
        coords = [
            top_left,
            (bottom_right[0], top_left[1]),
            bottom_right,
            (top_left[0], bottom_right[1]),
        ]
        self.add_named_poly(coords, layer, name)

    def add_named_poly(self, coords, layer, name):
        poly = sg.Polygon(coords)
        self.layers[layer].add_named(poly, name)

    def add_part(self, xy, part, side="top", rot=None, val=None, **kwargs):
        if isinstance(xy, Draw):
            return part(xy, val=val, side=side, **kwargs)
        if rot is not None:
            return part(self.DC(xy).right(rot), val=val, side=side, **kwargs)
        return part(self.DC(xy), val=val, side=side, **kwargs)

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

    def add_keepout(self, top_left, bottom_right, layer):
        coords = [
            top_left,
            (bottom_right[0], top_left[1]),
            bottom_right,
            (top_left[0], bottom_right[1]),
        ]
        poly = sg.Polygon(coords)
        self.layers[layer].keepouts.append(poly)

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
        angle=0.0,
        side="top",
        layer=None,
        keepout_box=False,
        soldermask_box=False,
        justify="centre",
    ):
        (x, y) = xy
        if justify == "left":
            gt = hershey.ltext(
                0, 0, text, scale=scale, side=side, linewidth=self.drc.text_silk_width
            )
        else:
            gt = hershey.text(
                0, 0, text, scale=scale, side=side, linewidth=self.drc.text_silk_width
            )
        gt = sa.rotate(gt, angle)
        gt = sa.translate(gt, x, y)
        lyr = layer if layer is not None else self.get_silk_layer(side, as_name=True)
        self.layers[lyr].add(gt)
        if keepout_box:
            self.add_keepout_to_obj(gt, layer=lyr)
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
        lyr = layer if layer is not None else self.get_silk_layer(side, as_name=True)
        self.layers[lyr].add(g)
        if keepout_box:
            self.add_keepout_to_obj(g, layer=lyr)
        if soldermask_box:
            self.add_mask_to_obj(g, side)

    #########################################################################
    #
    # Save Output Assets Methods
    #
    #########################################################################

    def _get_asset_path(self, basename, in_subdir=True, subdir=None):
        if in_subdir:
            if subdir is not None:
                newpath = os.path.normpath("./%s" % (subdir))
            else:
                newpath = os.path.normpath("./%s" % (basename))
            if not os.path.isdir(newpath):
                try:
                    os.mkdir(newpath)
                except OSError:
                    print("Directory %s cannot be created" % (newpath))
            if subdir is not None:
                assetpath = os.path.normpath("./%s" % (subdir) + os.sep + basename)
            else:
                assetpath = os.path.normpath("./%s" % (basename) + os.sep + basename)
        else:
            assetpath = basename
        return assetpath

    def save(
        self,
        basename,
        in_subdir=True,
        gerber=True,
        pdf=True,
        bom=True,
        centroids=True,
        povray=False,
        subdir=None,
    ):
        assetpath = self._get_asset_path(basename, in_subdir, subdir=subdir)

        if gerber:
            self.save_gerbers(basename, in_subdir, subdir=subdir)

        if pdf:
            self.save_pdf(basename, in_subdir, subdir=subdir)

        if povray:
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
        if bom:
            self.save_bom(basename, in_subdir, subdir=subdir)
        if centroids:
            self.save_centroids(basename, in_subdir, subdir=subdir)

    def save_gerbers(self, basename, in_subdir=True, subdir=None):
        assetpath = self._get_asset_path(basename, in_subdir, subdir=subdir)

        for name, layer in self.layers.items():
            print("Rendering Gerber %s..." % (name))
            if name == "GTD":
                fn = assetpath + "_top.GBR"
            elif name == "GBD":
                fn = assetpath + "_bot.GBR"
            else:
                fn = assetpath + "." + name
            with open(fn, "wt") as f:
                layer.save(f)
        ls = "1,%d" % (len(self.get_copper_layers()))
        print("Rendering excellon drill files...")
        with open(assetpath + "_PTH.DRL", "wt") as f:
            excellon(f, self.holes, "Plated,%s,PTH" % (ls))
        with open(assetpath + "_NPTH.DRL", "wt") as f:
            excellon(f, self.npth, "NonPlated,%s,NPTH" % (ls))

    def save_pdf(self, basename, in_subdir=True, subdir=None):
        self.save_svg(basename, in_subdir=in_subdir, formats=["pdf"], subdir=subdir)

    def save_png(self, basename, in_subdir=True, subdir=None):
        self.save_svg(basename, in_subdir=in_subdir, formats=["png"], subdir=subdir)

    def save_svg(self, basename, in_subdir=True, formats=["svg"], subdir=None):
        assetpath = self._get_asset_path(basename, in_subdir, subdir=subdir)

        from pcbflow.svgout import svg_write

        print("Rendering preview_top.%s..." % (formats))
        svg_write(self, assetpath + "_preview_top.svg", style="top", formats=formats)
        print("Rendering preview_top_docu.%s..." % (formats))
        svg_write(
            self,
            assetpath + "_preview_top_docu.svg",
            style="top_docu",
            formats=formats,
        )
        print("Rendering preview_bot.%s..." % (formats))
        svg_write(self, assetpath + "_preview_bot.svg", style="bottom", formats=formats)
        print("Rendering preview_bot_docu.%s..." % (formats))
        svg_write(
            self,
            assetpath + "_preview_bot_docu.svg",
            style="bottom_docu",
            formats=formats,
        )
        print("Rendering preview_all.%s..." % (formats))
        svg_write(self, assetpath + "_preview_all.svg", style="all", formats=formats)

    def save_centroids(self, basename, in_subdir=True, subdir=None):
        fn = self._get_asset_path(basename, in_subdir, subdir=subdir)
        with open(fn + "-centroids.csv", "wt") as f:
            cs = csv.writer(f)
            cs.writerow(
                ["Designator", "Center(X)", "Center(Y)", "Rotatation", "Layer", "Note"]
            )

            def flt(x):
                return "{:.3f}".format(better_float(x))

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

    def save_bom(self, basename, in_subdir=True, subdir=None):
        fn = self._get_asset_path(basename, in_subdir, subdir=subdir)
        parts = defaultdict(list)
        rank = "UJKTRCMYB"
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

    #########################################################################
    #
    # Misc Methods
    #
    #########################################################################

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

    def oversize(self, r):
        self.layers["GML"].add(self.boundary(r))
        sr = self.drc.silk_width / 2
        g = self.boundary(1.1 * sr).buffer(sr)
        self.layers["GTO"].add(g.buffer(0))

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
        h = math.sqrt(2 * (y**2))

        z[0].w("o f .2 l 45 f {0} r 45 f .1".format(h))
        z[1].w("o f .2 r 45 f {0} l 45 f .1".format(h))
        assert (abs(c - z[0].distance(z[1]))) < 1e-3
        return Route(self, z)

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
