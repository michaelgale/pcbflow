#! /usr/bin/env python3
#
# SVG file exporter
#

import decimal
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so
import svgwrite

from pcbflow import *

SCALE_FACTOR = 4

SVG_STYLE = {
    "top": [
        ("GTL", "indianred", "indianred", 1.0),
        ("GTS", "dimgray", "darkgray", 0.3),
        ("GTP", "mintcream", "lightcyan", 0.3),
        ("GTO", "darkkhaki", "darkkhaki", 1.0),
        ("DRL", "black", "black", 1.0),
        ("GML", "white", "slategray", 0.0),
    ],
    "top_docu": [
        ("GTL", "indianred", "indianred", 1.0),
        ("GTO", "darkkhaki", "darkkhaki", 1.0),
        ("GTD", "yellow", "yellow", 1.0),
        ("DRL", "black", "black", 1.0),
        ("GML", "white", "slategray", 1.0),
    ],
    "bottom_docu": [
        ("GBL", "royalblue", "royalblue", 1.0),
        ("GBO", "darkkhaki", "darkkhaki", 1.0),
        ("GBD", "yellow", "yellow", 1.0),
        ("DRL", "black", "black", 1.0),
        ("GML", "white", "slategray", 1.0),
    ],
    "bottom": [
        ("GBL", "royalblue", "royalblue", 1.0),
        ("GBS", "dimgray", "darkgray", 0.3),
        ("GBP", "mintcream", "lightcyan", 0.3),
        ("GBO", "darkkhaki", "darkkhaki", 1.0),
        ("DRL", "black", "black", 1.0),
        ("GML", "white", "slategray", 1.0),
    ],
    "all": [
        ("GBO", "darkkhaki", "darkkhaki", 1.0),
        ("GBS", "dimgray", "darkgray", 0.5),
        ("GBP", "mintcream", "lightcyan", 0.5),
        ("GBL", "royalblue", "royalblue", 0.4),
        ("GP3", "chocolate", "chocolate", 0.4),
        ("GP2", "green", "green", 0.4),
        ("GTL", "indianred", "indianred", 0.4),
        ("GTS", "dimgray", "darkgray", 0.3),
        ("GTP", "mintcream", "lightcyan", 0.3),
        ("GTO", "darkkhaki", "darkkhaki", 1.0),
        ("DRL", "black", "black", 1.0),
        ("GML", "white", "slategray", 0.0),
    ],
}


def svg_write(board, filename, style="top"):
    gml = board.layers["GML"].lines
    block = sg.Polygon(gml[-1], gml[:-1])
    block = block.buffer(1).buffer(-1)
    for d, xys in board.holes.items():
        if d > 0.1:
            hlist = so.unary_union([sg.Point(xy).buffer(d / 2) for xy in xys])
            block = block.difference(hlist)

    block = sa.scale(block, SCALE_FACTOR, -SCALE_FACTOR, origin=(0, 0))
    (x0, y0, x1, y1) = block.bounds
    block = sa.translate(block, -x0, -y0)
    x1 -= x0
    y1 -= y0

    args = {
        "stroke": "slategray",
        "fill_opacity": 0.0,
        "stroke_width": 0.1 * SCALE_FACTOR,
    }
    dwg = svgwrite.Drawing(
        filename, size=("%fmm" % x1, "%fmm" % y1), viewBox=("0 0 %f %f" % (x1, y1))
    )
    li = [block.exterior] + list(block.interiors)
    for l in li:
        dwg.add(dwg.polyline(better_coords(l.coords), **args))

    def renderlayer(layer, fill_colour="black", line_colour="black", fill_opacity=1.0):
        gto = board.layers[layer].preview()
        gto = sa.scale(gto, SCALE_FACTOR, -SCALE_FACTOR, origin=(0, 0))
        gto = sa.translate(gto, -x0, -y0)

        args = {
            "fill": fill_colour,
            "fill_opacity": fill_opacity,
            "stroke": fill_colour,
            "stroke_opacity": 0,
            "stroke_width": 0,
        }

        def renderpoly(po):
            if type(po) == sg.MultiPolygon:
                [renderpoly(p) for p in po]
                return

            if len(po.interiors) == 0:
                dwg.add(dwg.polygon(better_coords(po.exterior.coords), **args))
            else:
                bc = better_coords(po.exterior.coords)
                x0 = min([x for (x, y) in bc])
                x1 = max([x for (x, y) in bc])
                y0 = min([y for (x, y) in bc])
                y1 = max([y for (x, y) in bc])
                xm = (x0 + x1) / 2
                eps = 0.0
                renderpoly(po.intersection(sg.box(x0, y0, xm + eps, y1)))
                renderpoly(po.intersection(sg.box(xm - eps, y0, x1, y1)))

        if isinstance(gto, sg.Polygon):
            renderpoly(gto)
        else:
            [renderpoly(po) for po in gto]
        args = {
            "stroke": line_colour,
            "fill_opacity": 0.0,
            "stroke_opacity": fill_opacity,
            "stroke_width": 0.1,
        }
        if not isinstance(gto, sg.Polygon):
            for po in gto:
                li = [po.exterior] + list(po.interiors)
                for l in li:
                    dwg.add(dwg.polyline(better_coords(l.coords), **args))

    # make a temporary DRL layer to render representations of holes
    board.layers["DRL"] = Layer()
    for d, xys in board.holes.items():
        dp = so.unary_union([sg.Point(xy).buffer(d / 2) for xy in xys])
        board.layers["DRL"].add(dp)
    for d, xys in board.npth.items():
        dp = so.unary_union([sg.Point(xy).buffer(d / 2) for xy in xys])
        board.layers["DRL"].add(dp)

    if style not in SVG_STYLE:
        raise KeyError("Cannot find a style called %s in SVG_STYLE" % (style))
    style = SVG_STYLE[style.lower()]
    for layer, fc, lc, op in style:
        if layer in board.layers:
            renderlayer(layer, fill_colour=fc, line_colour=lc, fill_opacity=op)

    dwg.save()
