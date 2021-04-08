#! /usr/bin/env python3
#
# KiCad part/footprint importer
#
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

from .sexp_parser import *
from pcbflow import *

KI_LAYER_DICT = {
    "F.SilkS": "GTO",
    "F.Paste": "GTP",
    "F.Mask": "GTS",
    "F.Cu": "GTL",
    "F.Fab": "GTD",
}


class KiCadPart(Part):
    def __init__(self, dc, val=None, source=None, libraryfile=None, **kwargs):
        self.libraryfile = libraryfile
        self.smd_pads = []
        self.pin_pads = []
        self.polys = []
        self.lines = []
        self.labels = []
        self.docu = []
        super().__init__(dc, val, source, **kwargs)

    def place(self, dc):
        self.parse()
        ls = []
        for line in self.lines:
            p0 = dc.copy().goxy(*line["coords"][0])
            p1 = dc.copy().goxy(*line["coords"][1])
            ls.append(sg.LineString([p0.xy, p1.xy]))
            g = sg.LineString([p0.xy, p1.xy]).buffer(self.board.drc.silk_width / 2)
            if "GTO" in line["layers"]:
                self.board.get_silk_layer(side=self.side).add(g)
            elif "GTD" in line["layers"]:
                self.board.get_docu_layer(side=self.side).add(g)
            elif "GTP" in line["layers"]:
                self.board.get_paste_layer(side=self.side).add(g)

        for pad in self.smd_pads:
            p = dc.copy().goxy(*pad["xy"])
            p.rect(*pad["size"])
            if "GTL" in pad["layers"]:
                p.set_name(pad["name"])
                no_paste = True if "GTP" not in pad["layers"] else False
                self.smd_pad(p, ignore_paste=no_paste)
            elif "GTP" in pad["layers"]:
                self.board.get_paste_layer(side=self.side).add(p.poly())                

        for pad in self.pin_pads:
            diameter = pad["size"][0]
            dc.push()
            dc.goxy(*pad["xy"])
            dc.board.add_drill(dc.xy, pad["drill"])
            shape = pad["shape"]
            if shape in ["long", "circle", "octagon", "rect"]:
                n = {"long": 60, "circle": 60, "octagon": 8, "rect": 4}[shape]
                if shape == "rect":
                    diameter /= 1.1
                p = dc.copy()
                p.n_agon(diameter / 2, n)
                p.set_name(pad["name"])
                p.part = self.id
                self.pads.append(p)
                p.pin_pad()
                dc.pop()

    def _map_layers(self, layers):
        ml = []
        for layer in layers:
            if layer in KI_LAYER_DICT:
                ml.append(KI_LAYER_DICT[layer])
        return ml

    def _parse_fp_circle(self, items):
        pass

    def _parse_fp_line(self, items):
        coords = []
        width = 0
        layers = []
        for e in items:
            if isinstance(e, dict):
                if "start" in e:
                    coord = e["start"]
                    x, y = float(coord[0]), float(coord[1])
                    coords.append((float(coord[0]), float(coord[1])))
                elif "end" in e:
                    coord = e["end"]
                    x, y = float(coord[0]), float(coord[1])
                    coords.append((float(coord[0]), float(coord[1])))
                elif "width" in e:
                    width = float(e["width"][0])
                elif "layer" in e:
                    layers = self._map_layers(e["layer"])
        if len(layers) > 0:
            self.lines.append({"coords": coords, "width": width, "layers": layers})

    def _parse_pad(self, items):
        xy = (0, 0)
        size = (0, 0)
        name = items[0]
        layers = []
        shape = ""
        drill = 0
        if items[1] == "smd":
            for e in items[2:]:
                if isinstance(e, dict):
                    if "at" in e:
                        xy = float(e["at"][0]), float(e["at"][1])
                    elif "size" in e:
                        size = float(e["size"][0]), float(e["size"][1])
                    elif "layers" in e:
                        layers = self._map_layers(e["layers"])
            self.smd_pads.append({"name": name, "xy": xy, "size": size, "layers": layers})

        elif items[1] == "thru_hole":
            shape = items[2]
            for e in items[3:]:
                if isinstance(e, dict):
                    if "at" in e:
                        xy = float(e["at"][0]), float(e["at"][1])
                    elif "size" in e:
                        size = float(e["size"][0]), float(e["size"][1])
                    # TODO: support oval shaped drill, i.e. slot
                    elif "drill" in e:
                        try:
                            drill = float(e["drill"][0])
                        except:
                            pass
            self.pin_pads.append(
                {"name": name, "xy": xy, "size": size, "drill": drill, "shape": shape}
            )

    def parse(self):
        with open(self.libraryfile, "r") as f:
            module = parseSexp(f.read())

        d = {str(k[0]): k[1:] for k in module if isinstance(k, list)}
        md = {}
        for k, v in d.items():
            vd = []
            for kk in v[1:]:
                if isinstance(kk, list):
                    vd.append({kk[1]: kk[2:]})
                else:
                    vd.append(kk)
            md[k] = {v[0]: vd}

        for k, v in md.items():
            if "fp_line" in v:
                self._parse_fp_line(v["fp_line"])
            if "pad" in v:
                self._parse_pad(v["pad"])

# TODO   (fp_arc (start 0 0) (end 0 4) (angle -65) (layer F.Fab) (width 0.1))
# TODO    (fp_circle (center 0 0) (end 1.12 0) (layer F.Fab) (width 0.1))
# TODO   (fp_text reference REF** (at 0 -2.82) (layer F.SilkS)
#     (effects (font (size 1 1) (thickness 0.15)))
#   )
#   (fp_poly (pts (xy 2.45 -2.51) (xy 4.45 -2.51) (xy 4.45 -5.15) (xy 7.15 -5.15)
#     (xy 7.15 -2.51) (xy 9.15 -2.51) (xy 9.15 -5.15) (xy 11.85 -5.15)
#     (xy 11.85 -0.71) (xy 11.35 -0.71) (xy 11.35 -4.65) (xy 9.65 -4.65)
#     (xy 9.65 -2.01) (xy 6.65 -2.01) (xy 6.65 -4.65) (xy 4.95 -4.65)
#     (xy 4.95 -2.01) (xy 1.95 -2.01) (xy 1.95 -4.65) (xy 0.25 -4.65)
#     (xy 0.25 0.25) (xy -0.25 0.25) (xy -0.25 -4.65) (xy -1.65 -4.65)
#     (xy -1.65 0.25) (xy -2.55 0.25) (xy -2.55 0.006785) (xy -2.247583 0.006785)
#     (xy -2.237742 0.054395) (xy -2.213674 0.096797) (xy -2.175731 0.129581) (xy -2.167819 0.133935)
#     (xy -2.125156 0.146043) (xy -2.076637 0.1453) (xy -2.031122 0.1324) (xy -2.012511 0.121787)
#     (xy -1.978868 0.086553) (xy -1.958309 0.041368) (xy -1.951778 -0.008158) (xy -1.960218 -0.056417)
#     (xy -1.977112 -0.088643) (xy -2.012372 -0.121313) (xy -2.057682 -0.141408) (xy -2.107267 -0.147982)
#     (xy -2.155353 -0.140092) (xy -2.188245 -0.123186) (xy -2.223185 -0.086416) (xy -2.242847 -0.041622)
#     (xy -2.247583 0.006785) (xy -2.55 0.006785) (xy -2.55 -5.15) (xy 2.45 -5.15)
#     (xy 2.45 -2.51)) (layer F.Cu) (width 0))
