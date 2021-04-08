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

        for pad in self.smd_pads:
            p = dc.copy().goxy(*pad["xy"])
            p.rect(*pad["size"])
            p.set_name(pad["name"])
            self.smd_pad(p)

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
            if "GTL" in layers:
                self.smd_pads.append({"name": name, "xy": xy, "size": size})
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
            # print(k, v)
            if "fp_line" in v:
                self._parse_fp_line(v["fp_line"])
            if "pad" in v:
                self._parse_pad(v["pad"])
