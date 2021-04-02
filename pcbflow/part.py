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

class Part:
    mfr = ""
    footprint = ""
    val = ""
    inBOM = True
    source = {}

    def __init__(self, dc, val=None, source=None, side="top"):
        self.id = dc.board.assign(self)
        self.side = side.lower()
        if val is not None:
            self.val = val
        self.pads = []
        self.board = dc.board
        self.center = dc.copy()
        self.place(dc)
        if source is not None:
            self.source = source

    def _layers(self):
        if self.side == "top":
            return ["GTL", "GTS", "GTP"]
        else:
            return ["GBL", "GBS", "GBP"]

    def _silklayer(self):
        if self.side == "top":
            return "GTO"
        return "GBO"

    def text(self, dc, s):
        (x, y) = dc.xy
        dc.board.layers[self._silklayer()].add(hershey.ctext(x, y, s))

    def label(self, dc):
        (x, y) = dc.xy
        dc.board.layers[self._silklayer()].add(hershey.ctext(x, y, self.id))

    def minilabel(self, dc, s):
        dc.push()
        dc.rect(0.7, 0.7)
        dc.silko(side=self.side)
        dc.w("r 180 f 1.5")
        (x, y) = dc.xy
        dc.board.layers[self._silklayer()].add(hershey.ctext(x, y, s))
        dc.pop()
        dc.newpath()

    def notate(self, dc, s):
        (x, y) = dc.xy
        dc.board.layers[self._silklayer()].add(hershey.text(x, y, s, scale=0.1))

    def chamfered(self, dc, w, h, drawid=True, idoffset=(0, 0)):
        # Outline in top silk, chamfer indicates top-left
        # ID next to chamfer

        nt = 0.4
        dc.push()
        dc.forward(h / 2)
        dc.left(90)
        dc.forward(w / 2 - nt)
        dc.right(180)
        dc.newpath()
        for e in (w - nt, h, w, h - nt):
            dc.forward(e)
            dc.right(90)
        dc.silko(side=self.side)
        dc.pop()

        dc.push()
        dc.forward(h / 2 + 0.5)
        dc.left(90)
        dc.forward(w / 2 + 0.5)
        dc.right(90)
        dc.goxy(*idoffset)
        (x, y) = dc.xy
        if drawid:
            dc.board.layers[self._silklayer()].add(hershey.ctext(x, y, self.id))
        dc.pop()

    def pad(self, dc, padsize=None, maskratio=1.0):
        for n in self._layers():
            if n.endswith("S"):
                if padsize is not None:
                    dc.rect(maskratio*padsize[0], maskratio*padsize[1])
                gs = dc.poly()
                dc.board.layers[n].add(gs)
            else:
                if padsize is not None:
                    dc.rect(*padsize)
                g = dc.poly()
                dc.board.layers[n].add(g)
        p = dc.copy()
        p.part = self.id
        self.pads.append(p)


    def rpad(self, dc, w, h):
        dc.right(90)
        dc.rect(w, h)
        self.pad(dc)
        dc.left(90)

    def roundpad(self, dc, d):
        (dc.w, dc.h) = (d, d)
        g = sg.Point(dc.xy).buffer(d / 2)
        for n in self._layers():
            dc.board.layers[n].add(g)
        p = dc.copy()
        p.part = self.id
        self.pads.append(p)

    def train(self, dc, n, op, step):
        for i in range(n):
            op()
            dc.forward(step)

    def s(self, nm):
        if " " in nm:
            return [self.s(n) for n in nm.split()]
        return {p.name: p for p in self.pads}[nm]


class Discrete2(Part):
    def escape(self, l0, l1):
        # Connections to GND and VCC
        [p.outside() for p in self.pads]
        self.pads[0].wvia(l0)
        self.pads[1].wvia(l1)


class C0402(Discrete2):
    family = "C"
    footprint = "0402"

    def place(self, dc):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(1.30 / 2)
            dc.rect(0.8, 0.8)
            self.pad(dc, padsize=(0.8, 0.8), maskratio=1.1)
            dc.pop()

        # Silk outline of the package
        dc.rect(1.0, 0.5)
        dc.silko(side=self.side)

        dc.push()
        dc.right(90)
        dc.forward(2.65)
        self.label(dc)
        dc.pop()

    def escape_2layer(self):
        # escape for 2-layer board (VCC on GTL, GND on GBL)
        self.pads[0].setname("VCC").w("o f 0.5").wire()
        self.pads[1].w("o -")


class C0603(Discrete2):
    family = "C"
    footprint = "0603"

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(1.70 / 2)
            dc.rect(1.0, 1.0)
            self.pad(dc, padsize=(1.0, 1.0), maskratio=1.2)
            dc.pop()

        # Silk outline of the package
        dc.rect(1.6, 0.8)
        dc.silko(side=self.side)

        dc.push()
        dc.right(90)
        dc.forward(2)
        self.label(dc)
        dc.pop()

class C1206(Discrete2):
    family = "C"
    footprint = "1206"

    def place(self, dc, source=None):
        # Pads on either side
        for d in (-90, 90):
            dc.push()
            dc.right(d)
            dc.forward(3.40 / 2)
            dc.rect(2.0, 2.0)
            self.pad(dc, padsize=(2.0, 2.0), maskratio=1.15)
            dc.pop()

        # Silk outline of the package
        dc.rect(3.2, 1.6)
        dc.silko(side=self.side)

        dc.push()
        dc.right(90)
        dc.forward(4)
        self.label(dc)
        dc.pop()

class R0402(C0402):
    family = "R"

class R0603(C0603):
    family = "R"

class R1206(C1206):
    family = "R"

class L0603(C0603):
    family = "L"

class L1206(C1206):
    family = "L"

# Taken from:
# https://www.analog.com/media/en/package-pcb-resources/package/pkg_pdf/ltc-legacy-qfn/QFN_64_05-08-1705.pdf


class QFN64(Part):
    family = "U"
    footprint = "QFN64"

    def place(self, dc):
        # Ground pad
        g = 7.15 / 3
        for i in (-g, 0, g):
            for j in (-g, 0, g):
                dc.push()
                dc.forward(i)
                dc.left(90)
                dc.forward(j)
                dc.square(g - 0.5)
                self.pad(dc)
                dc.via("GL2")
                dc.pop()
        self.pads = self.pads[:1]

        # Silk outline of the package
        self.chamfered(dc, 9, 9)
        # self.chamfered(dc, 7.15, 7.15)

        for i in range(4):
            dc.left(90)
            dc.push()
            dc.forward(8.10 / 2)
            dc.forward(0.70 / 2)
            dc.right(90)
            dc.forward(7.50 / 2)
            dc.left(180)
            self.train(dc, 16, lambda: self.rpad(dc, 0.25, 0.70), 0.50)
            dc.pop()


BT815pins = [
    "GND",
    "R0",
    "+1V2",
    "E_SCK",
    "E_MISO",
    "E_MOSI",
    "E_CS",
    "E_IO2",
    "E_IO3",
    "3V3",
    "",
    "E_INT",
    "E_PD",
    "",
    "M_SCK",
    "M_CS",
    "M_MOSI",
    "3V3",
    "M_MISO",
    "M_IO2",
    "M_IO3",
    "X1",  # X1: in
    "",  # X2: out
    "GND",
    "3V3",
    "+1V2",
    "AUDIO",
    "3V3",
    "3V3",
    "CTP_RST",
    "CTP_INT",
    "CTP_SCL",
    "CTP_SDA",
    "GND",
    "",
    "DE",
    "VSYNC",
    "HSYNC",
    "",
    "PCLK",
    "B7",
    "B6",
    "B5",
    "B4",
    "B3",
    "B2",
    "B1",
    "B0",
    "GND",
    "G7",
    "G6",
    "G5",
    "G4",
    "G3",
    "G2",
    "G1",
    "G0",
    "+1V2",
    "R7",
    "R6",
    "R5",
    "R4",
    "R3",
    "R2",
    "R1",
]


class BT815(QFN64):
    source = {"BridgeTek": "BT815Q"}
    mfr = "BT815Q"

    def escape(self):
        brd = self.board

        assert len(BT815pins) == len(self.pads)
        for p, n in zip(self.pads, BT815pins):
            p.setname(n)

        dc = self.pads[23]
        dc.right(180)
        dc.forward(2)
        dc.wire()

        dc = self.pads[33]
        dc.right(180)
        dc.forward(0.65)
        dc.right(45)
        dc.forward(1)
        dc.wire()

        dc = self.pads[48]
        dc.right(180)
        dc.forward(0.65)
        dc.left(45)
        dc.forward(1)
        dc.wire()

        def backside(dc, d):
            dc.newpath()
            dc.push()
            dc.right(180)
            dc.forward(0.35 + 0.2)
            dc.right(90)
            dc.forward(d * 0.5)
            dc.right(90)
            dc.forward(0.35 + 0.2)
            dc.wire()
            dc.pop()

        def via(dc, l):
            dc.push()
            dc.forward(0.35)
            dc.forward(brd.via_space + brd.via / 2)
            dc.wire()
            dc.via(l)
            dc.pop()

        # VCC
        backside(self.pads[24], 3)
        backside(self.pads[24], 4)

        for i in (9, 17, 27):
            dc = self.pads[i]
            via(dc, "GL3")

        for i, sig in enumerate(BT815pins):
            if sig == "+1V2":
                via(self.pads[i], "GBL")

        power = {"3V3", "GND", "", "+1V2"}
        spim = {"M_SCK", "M_CS", "M_MOSI", "M_MISO", "M_IO2", "M_IO3"}
        ctp = ["CTP_RST", "CTP_INT", "CTP_SCL", "CTP_SDA"]

        sctp = [self.s(nm) for nm in ctp]
        for i, s in enumerate(sctp):
            s.w("o f 0.4").forward(0.5 * (i & 1)).wire()
            s.via().setlayer("GBL").w("f 0.7")
        extend2(sctp)
        rctp = brd.enriver90(sctp, -90)
        rctp.wire()

        ext = [
            i for i, sig in enumerate(BT815pins) if sig not in (power | spim | set(ctp))
        ]
        spi = [i for i, sig in enumerate(BT815pins) if sig in spim]
        for i in ext:
            self.pads[i].forward(1)
            self.pads[i].wire()
        # self.s("AUDIO").forward(.5)
        [self.pads[i].outside() for i in spi]

        def bank(n, pool):
            return [self.pads[i] for i in pool if (i - 1) // 16 == n]

        rv0 = brd.enriver90(bank(0, ext), 90)
        rv1 = brd.enriver90(bank(1, ext), -90)
        rv2 = brd.enriver(bank(2, ext), -45)
        rv3 = brd.enriver(bank(3, ext), 45)
        rv0.w("f .2 r 45 f .3").wire()

        rv1.w("r 45 f 1.0 l 45 f 2.5 l 45 f 3 l 45 f 1.2 r 45")
        rv1.wire()

        rv2 = rv1.join(rv2, 1)

        rv2.forward(0.6)

        rv0.forward(1).shimmy(0.344)
        rv3.shimmy(0.344)
        rv23 = rv2.join(rv3, 1.0)
        rv230 = rv23.join(rv0)
        rv230.wire()

        rv4 = brd.enriver90(bank(0, spi), -90)
        rv4.w("f 1 l 45")
        rv5 = brd.enriver(bank(1, spi), -45)
        rvspi = rv4.join(rv5)

        GBL = self.board.layers["GBL"]
        dc = self.center.copy()
        dc.rect(12, 12)
        GBL.add(GBL.paint(dc.poly(), "GBL", self.board.via_space))
        dc.layer = "GBL"

        return (rvspi, rv230, rctp)


# IPC-SM-782A section 9.1: SOIC


class SOIC(Part):
    family = "U"
    footprint = "SOIC-8"

    def place(self, dc):

        self.chamfered(dc, self.A, self.B)
        for _ in range(2):
            dc.push()
            dc.forward(self.D / 2)
            dc.left(90)
            dc.forward(self.C / 2)
            dc.left(90)
            self.train(dc, self.N // 2, lambda: self.rpad(dc, 0.60, 2.20), 1.27)
            dc.pop()
            dc.right(180)


class SOIC8(SOIC):
    N = 8

    A = 4.0
    B = 5.0
    C = 5.90
    D = 3.81
    G = 3.0
    Z = 7.4


class TSSOP(Part):
    family = "U"

    def place(self, dc):
        self.chamfered(dc, 4.4, {14: 5.0, 20: 6.5}[self.N])
        P = self.N // 2
        e = 0.65
        for _ in range(2):
            dc.push()
            dc.forward(e * (P - 1) / 2)
            dc.left(90)
            dc.forward((4.16 + 1.78) / 2)
            dc.left(90)
            self.train(dc, P, lambda: self.rpad(dc, 0.42, 1.78), e)
            dc.pop()
            dc.right(180)


class TSSOP14(TSSOP):
    N = 14


class M74VHC125(TSSOP14):
    def escape(self):
        for p, s in zip(
            self.pads, "A0 B0 O0 A1 B1 O1 GND  O3 B3 A3 O2 B2 A2 VCC".split()
        ):
            p.setname(s)
        self.s("VCC").w("o f 1")
        for p in self.pads:
            if p.name in ("GND", "A0", "A1", "A2", "A3"):
                p.w("o -")

        self.s("O0").w("i f 0.4 l 90 f 3")
        self.s("O1").w("i f 1.2 l 90 f 3")
        self.s("O3").w("i f 1.2 r 90 f 3")
        self.s("O2").w("i f 0.4 r 90 f 3")
        outs = self.s("O2 O3 O1 O0")
        extend2(outs)
        rout = self.board.enriver90(outs, 90)

        self.s("B0").w("o f 1.2 . l 90 f 2").wire(layer="GBL")
        self.s("B1").w("o f 0.6 . l 90 f 2").wire(layer="GBL")
        self.s("B3").w("o f 0.6 . r 90 f 2").wire(layer="GBL")
        self.s("B2").w("o f 1.2 . r 90 f 2").wire(layer="GBL")

        ins = self.s("B0 B1 B3 B2")
        extend2(ins)
        rin = self.board.enriver90(ins, -90)

        [p.wire() for p in self.pads]
        return (rin, rout)


class SOT764(Part):
    family = "U"

    def place(self, dc):
        self.chamfered(dc, 2.5, 4.5)
        # pad side is .240 x .950

        def p():
            dc.rect(0.240, 0.950)
            self.pad(dc)

        for i in range(2):
            dc.push()
            dc.goxy(-0.250, (3.5 + 1.0) / 2)
            p()
            dc.pop()

            dc.push()
            dc.goxy(-(1.7 / 2 + 0.5), 3.5 / 2)
            dc.right(180)
            self.train(dc, 8, lambda: self.rpad(dc, 0.240, 0.950), 0.5)
            dc.pop()

            dc.push()
            dc.goxy(-0.250, -(3.5 + 1.0) / 2).right(180)
            p()
            dc.pop()
            dc.right(180)


class M74LVC245(SOT764):
    source = {"LCSC": "C294612"}
    mfr = "74LVC245ABQ"

    def escape(self):
        names = [
            "DIR",
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "GND",
            "B7",
            "B6",
            "B5",
            "B4",
            "B3",
            "B2",
            "B1",
            "B0",
            "OE",
            "VCC",
        ]
        [p.setname(nm) for (p, nm) in zip(self.pads, names)]
        [p.outside() for p in self.pads]
        self.s("GND").w("o -")
        self.s("OE").w("l 90 f 0.4 -")
        self.s("VCC").w("o f 0.5").wire()
        self.s("DIR").setname("VCC").w("o f 0.5").wire()

        gin = [self.s(nm) for nm in ("A6", "A5", "A4", "A3", "A2", "A1", "A0")]
        [
            s.forward(0.2 + 0.8 * i).w("l 45 f .2 .").w("f .2").wire("GBL")
            for (i, s) in enumerate(gin)
        ]
        extend2(gin)
        ins = self.board.enriver90(gin[::-1], -90).w("r 45").wire()

        # self.s("B7").w("l 90 f 1.56").wire()
        gout = [self.s(nm) for nm in ("B6", "B5", "B4", "B3", "B2", "B1", "B0")]
        [s.forward(0.2) for s in gout]
        outs = self.board.enriver90(gout, 90).wire()

        return (ins, outs)

    def escape2(self):
        names = [
            "DIR",
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "GND",
            "B7",
            "B6",
            "B5",
            "B4",
            "B3",
            "B2",
            "B1",
            "B0",
            "OE",
            "VCC",
        ]
        [p.setname(nm) for (p, nm) in zip(self.pads, names)]
        [p.outside() for p in self.pads]
        self.s("GND").w("o -")
        self.s("OE").w("l 90 f 0.4 -")
        self.s("VCC").w("o f 0.5").wire()

        gin = [self.s(nm) for nm in ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7")]
        extend2(gin)
        ins = self.board.enriver90(gin, 90)

        # self.s("B7").w("l 90 f 1.56").wire()
        self.s("B7").w("l 90 f 0.9").wire()
        gout = [self.s(nm) for nm in ("B7", "B6", "B5", "B4", "B3", "B2", "B1", "B0")]
        # [s.forward(0.2) for s in gout]
        extend2(gout)

        outs = self.board.enriver90(gout, 90).wire()

        return (ins, self.s("DIR"), outs)


class W25Q64J(SOIC8):
    source = {"LCSC": "C179171"}
    mfr = "W25Q64JVSSIQ"

    def escape(self):
        nms = "CS MISO IO2 GND MOSI SCK IO3 VCC".split()
        sigs = {nm: p for (nm, p) in zip(nms, self.pads)}

        for (nm, p) in zip(nms, self.pads):
            p.setname(nm)

        sigs["SCK"].w("r 90 f 0.3 l 90 f 1.1")
        sigs["CS"].w("i f 1.5 r 90 f 1.27 f 1.27 f .63 l 90 f .1")
        sigs["MISO"].w("i f 1.0 r 90 f 1.27 f 1.27 f .63 l 90 f .1")
        sigs["MOSI"].w("o f .1")
        sigs["IO2"].w("i f 0.5 r 90 f 2.20 l 90 f .1")
        sigs["IO3"].w("i f 0.5 r 90 f 1.27 f .63 l 90 f 6.5 l 90 f 5.65 l 90 f .1")
        sigs["GND"].w("o -")
        sigs["VCC"].w("f -.4 l 90 f 0.5 +")

        proper = (
            sigs["IO3"],
            sigs["IO2"],
            sigs["MISO"],
            sigs["MOSI"],
            sigs["CS"],
            sigs["SCK"],
        )
        extend(sigs["SCK"], proper)
        rv = self.board.enriver(proper, 45)
        rv.wire()
        return rv

    def escape1(self):
        b = self.board

        nms = "CS MISO IO2 GND MOSI SCK IO3 VCC".split()
        sigs = {nm: p for (nm, p) in zip(nms, self.pads)}
        for (nm, p) in zip(nms, self.pads):
            p.setname(nm)

        sigs["GND"].w("o -")
        sigs["VCC"].w("o +")

        ls = ("CS", "MISO", "IO2")
        rs = ("MOSI", "SCK", "IO3")

        for s in ls:
            sigs[s].w("i l 90 f 0.63 r 90").wire()
        for s in rs:
            sigs[s].w("i").wire()
        dv = b.via_space + b.via / 2
        for s in ls + rs:
            sigs[s].forward(dv)
        width = 3.7 - 2 * dv

        ord = "MOSI SCK MISO IO2 IO3 CS".split()
        gap = width / (len(ord) - 1)
        for i, s in enumerate(ord):
            x = i * gap
            if s in ls:
                x = width - x
            sigs[s].forward(x).wire().via("GBL")
            sigs[s].wire()
            if s in ls:
                sigs[s].right(180)
            sigs[s].right(90).forward(dv).wire("GBL")

        grp = [sigs[n] for n in ord]
        extend(grp[-1], grp)
        return self.board.enriver90(grp, -90).right(45).wire()


class HDMI(Part):
    family = "J"
    mfr = "HDMI-001"
    source = {"LCSC": "C138388"}

    def place(self, dc):
        self.chamfered(dc, 15, 11.1)

        def mounting(dc, l):
            dc.push()
            dc.newpath()
            dc.forward(l / 2)
            dc.right(180)
            dc.forward(l)
            dc.platedslot(0.5)
            dc.pop()

        # mounting(dc, 2)
        dc.push()
        dc.right(90)
        dc.forward(4.5)
        dc.left(90)
        dc.forward(5.35)
        dc.left(90)
        self.train(dc, 19, lambda: self.rpad(dc, 0.30, 2.60), 0.50)
        dc.pop()

        dc.right(90)
        dc.forward(14.5 / 2)
        dc.left(90)
        dc.forward(5.35 + 1.3 - 2.06)
        dc.right(180)

        def holepair():
            dc.push()
            mounting(dc, 2.8 - 1)
            dc.forward(5.96)
            mounting(dc, 2.2 - 1)
            dc.pop()

        holepair()
        dc.right(90)
        dc.forward(14.5)
        dc.left(90)
        holepair()
        dc.forward(5.96 + 3.6)
        dc.left(90)

        dc.newpath()
        dc.forward(14.5)
        dc.silk()

    def escape(self):
        board = self.board
        gnd = (1, 4, 7, 10, 13, 16)
        for g, p in zip(gnd, ["TMDS2", "TMDS1", "TMDS0", "TMDS_CLK"]):
            self.pads[g].setname("GND")
            self.pads[g - 1].setname(p + "_P")
            self.pads[g + 1].setname(p + "_N")

        for g in gnd:
            self.pads[g].w("i -")

        def pair(g):
            p = self.pads
            return self.board.enriverPair((p[g - 1], p[g + 1]))

        return ([pair(g) for g in gnd[:4]], self.pads[18])


class SOT223(Part):
    family = "U"
    footprint = "SOT223"

    def place(self, dc):
        self.chamfered(dc, 6.30, 3.30)
        dc.push()
        dc.forward(6.2 / 2)
        dc.rect(3.6, 2.2)
        self.pad(dc)
        dc.pop()

        dc.push()
        dc.left(90)
        dc.forward(4.60 / 2)
        dc.left(90)
        dc.forward(6.2 / 2)
        dc.left(90)
        self.train(dc, 3, lambda: self.rpad(dc, 1.20, 2.20), 2.30)
        dc.pop()

    def escape(self):
        # Returns (input, output) pads
        self.pads[2].w("i f 4").wire(width=0.8)
        self.pads[1].inside().fan(1.0, "GL2")
        self.pads[1].wire(width=0.8)
        return (self.pads[3], self.pads[0])


class FTG256(Part):
    family = "U"
    footprint = "FTG256"

    def place(self, dc):
        self.chamfered(dc, 17, 17)
        dc.left(90)
        dc.forward(7.5)
        dc.right(90)
        dc.forward(7.5)
        dc.right(90)
        for j in range(16):
            dc.push()
            for i in range(16):
                dc.left(90)
                self.roundpad(dc, 0.4)
                dc.right(90)
                dc.forward(1)
            dc.pop()
            dc.right(90)
            dc.forward(1)
            dc.left(90)

        return


class XC6LX9(FTG256):
    mfr = "XC6SLX9-2FTG256C"
    source = {"WIN SOURCE": "XC6SLX9-2FTG256C"}

    def collect(self, pp):
        p0 = pp[0]
        return [p for (_, p) in sorted([(p.seek(p0)[0], p) for p in pp])]

    def escape(self):
        north = self.pads[0].dir
        done = [False for _ in self.pads]

        FGname = "ABCDEFGHJKLMNPRT"
        padname = {
            FGname[i] + str(1 + j): self.pads[16 * i + j]
            for i in range(16)
            for j in range(16)
        }
        self.signals = {}
        for l in open("6slx9ftg256pkg.txt", "rt"):
            (pad, _, _, signal) = l.split()
            self.signals[pad] = signal

        for (pn, s) in self.signals.items():
            padname[pn].setname(s)

        powernames = (
            "GND",
            "VCCO_0",
            "VCCO_1",
            "VCCO_2",
            "VCCO_3",
            "VCCAUX",
            "VCCINT",
            "IO_L1P_CCLK_2",
            "IO_L3P_D0_DIN_MISO_MISO1_2",
            "IO_L3N_MOSI_CSI_B_MISO0_2",
            "IO_L65N_CSO_B_2",
            "IO_L49P_D3_2",
            "IO_L63P_2",
            "TCK",
            "TDI",
            "TMS",
            "TDO",
            "PROGRAM_B_2",
            "SUSPEND",
            "IO_L1N_M0_CMPMISO_2",  # M0 to VCC
            "IO_L13P_M1_2",  # M1 to GND
        )

        def isio(s):
            return s.startswith("IO_") and s not in powernames

        ios = {s for (pn, s) in self.signals.items() if isio(s)}
        unconnected = {"CMPCS_B_2", "DONE_2"}
        assert (set(self.signals.values()) - ios - set(powernames)) == unconnected

        byname = {s: padname[pn] for (pn, s) in self.signals.items()}
        self.padnames = padname

        if 0:
            for pn, s in self.signals.items():
                p = padname[pn]
                if s.startswith("IO_"):
                    f = s.split("_")
                    self.notate(p, f[1] + "." + f[-1])
                else:
                    self.notate(p, pn + "." + s)

        specials = [
            ("IO_L1P_CCLK_2", "SCK"),
            ("IO_L3P_D0_DIN_MISO_MISO1_2", "MISO"),
            ("IO_L3N_MOSI_CSI_B_MISO0_2", "MOSI"),
            ("IO_L65N_CSO_B_2", "CS"),
            ("IO_L49P_D3_2", "IO2"),
            ("IO_L63P_2", "IO3"),
            ("TCK", "TCK"),
            ("TDI", "TDI"),
            ("TMS", "TMS"),
            ("TDO", "TDO"),
        ]
        if 0:
            for (nm, lbl) in specials:
                self.minilabel(byname[nm], lbl)
        if 0:
            self.minilabel(byname["IO_L32N_M3DQ15_3"], "PCLK")
        if 0:
            for nm, p in byname.items():
                if "GCLK" in nm:
                    self.minilabel(p, "C")
        if 0:
            for pn, s in self.signals.items():
                p = padname[pn]
                self.notate(p, pn)

        for pn, s in self.signals.items():
            if s in powernames:
                p = padname[pn]
                if pn in ("R6", "R8"):
                    p.right(180 - 25.28)
                    p.forward(0.553)
                else:
                    p.right(45)
                    p.forward(math.sqrt(2) / 2)
                p.wire()
                dst = {
                    "GND": "GL2",
                    "IO_L13P_M1_2": "GL2",
                    "SUSPEND": "GL2",
                    "IO_L1N_M0_CMPMISO_2": "GL3",
                    "PROGRAM_B_2": "GBL",
                    "VCCINT": "GBL",
                    "IO_L1P_CCLK_2": "GBL",
                    "IO_L3P_D0_DIN_MISO_MISO1_2": "GBL",
                    "IO_L3N_MOSI_CSI_B_MISO0_2": "GBL",
                    "IO_L65N_CSO_B_2": "GBL",
                    "IO_L49P_D3_2": "GBL",
                    "IO_L63P_2": "GBL",
                    "TCK": "GBL",
                    "TDI": "GBL",
                    "TMS": "GBL",
                    "TDO": "GBL",
                }.get(s, "GL3")
                p.via(dst)

        GBL = self.board.layers["GBL"]
        dc = self.center.copy()
        dc.w("f 0.5 l 90")
        dc.rect(3, 23)
        GBL.add(GBL.paint(dc.poly(), "GBL", self.board.via_space))
        dc.layer = "GBL"

        v12 = dc
        v12.outside().newpath()

        d1 = math.sqrt(2 * (0.383 ** 2))
        d2 = math.sqrt(2 * ((1 - 0.383) ** 2))

        s1 = "f 0.500"
        s2 = "l 45  f {0} r 45 f 1.117".format(d1)
        s3 = "l 45  f {0} r 45 f 1.883".format(d2)
        s3s = "l 90  f .637 r 90  f {0} f 1.883".format(1 - 0.383)

        plan = (
            (0, ".1$", "l 90 " + s1),
            (0, "R2", "l 90 " + "r 45  f {0} l 45 f 1.117".format(d1)),
            (0, ".2$", "l 90 " + s2),
            (0, "[JL]3$", "l 90 " + "l 45 f {0} r 45 f 2.117".format(d1)),
            (0, "[KM]3$", "l 90 " + "r 45 f {0} l 45 f 2.117".format(d1)),
            (0, ".3$", "l 90 " + s3),
            (1, "T", "r 180 " + s1),
            (1, "R", "r 180 " + s2),
            (1, "P", "r 180 " + s3),
            (2, ".16$", "r 90 " + s1),
            (2, ".15$", "r 90 " + s2),
            (2, ".14$", "r 90 " + s3),
            (3, "A", s1),
            (3, "B", s2),
            (3, "C", s3),
        )
        keepout = (
            self.pads[0]
            .board.layers["GL2"]
            .preview()
            .union(self.pads[0].board.layers["GL3"].preview())
        )
        outer = {i: [] for i in range(4)}
        for pn, sig in self.signals.items():
            if isio(sig):
                for grp, pat, act in plan:
                    if re.match(pat, pn):
                        p = padname[pn]
                        p.push()
                        p.w(act)
                        if p.preview().intersects(keepout):
                            p.pop()
                        else:
                            outer[grp].append(p)
                            break

        board = self.pads[0].board
        oc = [self.collect(outer[i]) for i in range(4)]
        x = 3
        oc = oc[x:] + oc[:x]
        ep0 = oc[0][-16]
        rv0 = board.enriver90(oc[0][-15:], -90)
        rv1 = board.enriver90(oc[1], -90)
        rem = 38 - len(rv1.tt)
        rv2 = board.enriver90(oc[2][:rem], 90)
        p0 = board.enriverS(oc[3][:7], -45)
        p1 = board.enriverS(oc[3][-7:], 45)

        # cand = sorted([p.name[1] for p in oc[2][rem:]])
        # [print(c) for c in cand if c[-1] == '2']

        # BT815 bus
        # rv1.forward(0.29)
        a = 0
        rv1.left(a).right(a)
        rv1.right(45)
        rv1.wire()

        rv2.w("f 1.8 l 45 f 2")
        rv2.wire()

        rv12 = rv1.join(rv2)
        rv12.wire()

        # LVDS
        def makepair(n, p):
            n = byname[n]
            p = byname[p]
            # self.notate(n, n.name[3:7])
            # self.notate(p, p.name[3:7])
            return board.enriverPair((n, p))

        lvds = [
            makepair("IO_L23N_2", "IO_L23P_2"),
            makepair("IO_L30N_GCLK0_USERCCLK_2", "IO_L30P_GCLK1_D13_2"),
            makepair("IO_L32N_GCLK28_2", "IO_L32P_GCLK29_2"),
            makepair("IO_L47N_2", "IO_L47P_2"),
        ]

        # Flash

        grp = []
        for s, d in [
            ("IO_L3P_D0_DIN_MISO_MISO1_2", 1.4),
            ("IO_L1P_CCLK_2", 2.2),
            ("IO_L3N_MOSI_CSI_B_MISO0_2", 1),
        ]:
            t = byname[s]
            t.w("l 45 f 0.500 l 90").forward(d).left(90).forward(0.1).wire("GBL")
            grp.append(t)
        extend(grp[-1], grp)
        [t.forward(0.8).wire("GBL") for t in grp]
        frv0 = board.enriver90(grp, 90)
        frv0.w("f 0.5 l 90").wire()

        # 'IO_L49P_D3_2'      # P5
        # 'IO_L63P_2'         # P4
        # 'IO_L65N_CSO_B_2'   # T3
        grp = [byname[s] for s in ("IO_L65N_CSO_B_2", "IO_L63P_2", "IO_L49P_D3_2")]
        grp[2].w("r 45 f 0.330 r 90 f 0.2").wire("GBL")
        for t in grp[:2]:
            t.w("r 45 f 0.500 r 90 f 0.2").wire("GBL")
        extend(grp[0], grp)
        [t.forward(0.3).wire("GBL") for t in grp]
        frv1 = board.enriver90(grp, -90)
        frv1.w("r 90").wire("GBL")

        frv = frv1.join(frv0, 0.75)
        frv.wire("GBL")

        program = byname["PROGRAM_B_2"]
        program.w("l 90 f 7.5 l 45 f 7").wire("GBL")

        # JTAG
        jtag = [byname[s] for s in ("TCK", "TDI", "TMS", "TDO")]
        [t.w("l 45 f 0.5").wire("GBL") for t in jtag]
        # [self.notate(t, t.name[1]) for t in jtag]
        byname["TDO"].w("f 0.5 l 45 f 0.707 r 45").wire()
        extend(jtag[2], jtag)
        jrv = board.enriver90(self.collect(jtag), -90).wire()

        return (rv12, lvds, p0, p1, ep0, rv0, frv, jrv, program, v12)

    def dump_ucf(self, basename):
        with open(basename + ".ucf", "wt") as ucf:
            nets = self.board.nets

            def netpair(d):
                if self.id in d:
                    mine = d[self.id]
                    nms = set(d.values())
                    if len(nms) > 1:
                        nms -= {mine}
                    (oth,) = tuple(nms)
                    return (mine, oth)

            mynets = [r for r in [netpair(dict(n)) for n in nets] if r]
            padname = {s: p for (p, s) in self.signals.items()}
            for (m, o) in mynets:
                if o in ("TMS", "TCK", "TDO", "TDI"):
                    continue
                if "TMDS" in o:
                    io = "TMDS_33"
                else:
                    io = "LVTTL"
                ucf.write(
                    'NET "{0}" LOC="{1}" | IOSTANDARD="{2}";\n'.format(
                        o, padname[m], io
                    )
                )


class Castellation(Part):
    family = "J"
    inBOM = False

    def place(self, dc):
        dc.w("l 90 f 0.4 r 90")

        def cp():
            dc.right(90)
            dc.rect(1.2, 1)
            p = dc.copy()
            p.part = self.id
            self.pads.append(p)
            dc.contact()
            dc.push()
            dc.forward(0.375)
            dc.board.hole(dc.xy, 0.7)
            dc.pop()
            dc.left(90)

        self.train(dc, self.val, cp, 2.0)

    def escape(self):
        c = self.board.c

        def label(p, s):
            dc = p.copy()
            dc.inside()
            (d, tf) = {90: (0.05, hershey.text), 180: (0.6, hershey.ctext)}[dc.dir]
            dc.forward(d)
            (x, y) = dc.xy
            dc.board.layers["GTO"].add(tf(x, y, s))

        cnt = self.board.counters

        def group(pi, a):
            if a < 0:
                pp = pi[::-1]
            else:
                pp = pi
            for i, p in enumerate(pp):
                label(p, p.name[1:])
            for i, p in enumerate(pp):
                p.w("l 90 f .450 l 90 f .450 r 45" + (" f .12 l 9" * 10) + " r 45")
                p.forward((1 + i) * c)
                p.left(a)
                p.wire()
            extend(pp[0], pp)
            rv = River(self.board, pi[::-1])
            rv.right(a)
            rv.wire()
            return rv

        gnd = len(self.pads) // 2
        dc = self.pads[gnd]
        label(dc, "GND")
        self.sidevia(dc, "-")

        for p in self.pads:
            if p != self.pads[gnd]:
                cnt["port"] += 1
                p.setname("P" + str(cnt["port"]))

        a = group(self.pads[:gnd], -90)
        b = group(self.pads[gnd + 1 :], 90)
        return (a, b)

    def sidevia(self, dc, dst):
        assert dst in "-+."
        dc.setwidth(0.6)
        for l in ("GTL", "GBL"):
            dc.push()
            dc.setlayer(l)
            dc.push()
            dc.w("f -0.3 r 90 f 0.4 " + dst)
            dc.pop()
            dc.w("f -0.3 l 90 f 0.4 " + dst)
            dc.pop()

    def escape1(self):
        pp = self.pads[::-1]
        names = "PGM TDI TDO TCK TMS".split()
        [t.setname(n) for t, n in zip(pp, names)]

        for t in pp:
            dc = t.copy().w("i f 0.6")
            (x, y) = dc.xy
            dc.board.layers["GTO"].add(hershey.ctext(x, y, t.name))
            t.w("i f 1").wire("GBL")

        return (self.board.enriver(pp[1:], 45).left(45).wire(), pp[0])

    def escape2(self):
        pp = self.pads

        def label(t, s):
            dc = t.copy().w("i f 0.6")
            (x, y) = dc.xy
            dc.board.layers["GTO"].add(hershey.ctext(x, y, s))

        label(pp[0], "3.3")
        label(pp[1], "GND")
        label(pp[2], "5V")

        for l in ("GTL", "GBL"):
            pp[0].push().setlayer(l).setwidth(0.6).w(
                "f -0.3 r 90 f 0.5 + f 0.5 +"
            ).pop()
        self.sidevia(pp[1], "-")
        return pp[2]

    def escape3(self):
        pp = self.pads[::-1]
        names = "SDA SCL INT RST".split()
        [t.setname(n) for t, n in zip(pp, names)]

        for t in pp:
            dc = t.copy().w("i f 0.6")
            (x, y) = dc.xy
            dc.board.layers["GTO"].add(hershey.ctext(x, y, t.name))
            t.w("i f 1").wire("GBL")

        return self.board.enriver(pp, 45).left(45).wire()


class WiiPlug(Part):
    family = "J"
    inBOM = False

    def place(self, dc):
        dc.rect(21, 10)
        self.board.keepouts.append(dc.poly().buffer(0))

        def finger():
            dc.right(90)
            dc.rect(1.6, 7)
            g = dc.poly()
            self.board.layers[dc.layer].add(g, dc.name)
            mask = dc.layer.replace("L", "S")
            self.board.layers[mask].add(g, dc.name)
            p = dc.copy()
            self.pads.append(p)
            p.part = self.id
            dc.left(90)

        dc.push()
        dc.w("l 90 f 2 r 180")
        dc.push()
        dc.setlayer("GTL")
        self.train(dc, 2, finger, 4)
        dc.pop()
        dc.setlayer("GBL")
        self.train(dc, 3, finger, 2)
        dc.pop()

        dc.goxy(-9.5, 4.8)
        F15 = " l 90 f 3 r 90 f 15 r 90 f 3 l 90 "
        dc.newpath()
        dc.w(
            "r 90 f 3.3 r 90 f 3.15 r 90 f 1 l 90 f 3.25 l 90 f 1 r 90 f 2 l 90 f 2.95 l 90 f 7.3 r 90 f 3.25"
        )
        dc.w(
            "f 3.25 r 90 f 7.3 l 90 f 2.95 l 90 f 2 r 90 f 1 l 90 f 3.25 l 90 f 1 r 90 f 3.15 r 90 f 3.3"
        )
        dc.w("r 90" + F15 + "r 90 f 19 r 90" + F15)
        self.board.layers["GML"].union(dc.poly())

    def escape(self):
        self.pads[0].setname("SCL").w("o f 2 .").setlayer("GBL")
        self.pads[1].setname("GND").w("o f 1 l 45 f 4 r 45 -")
        self.pads[2].setname("VCC").w("o f 0.2 r 45 f 0.6 +").setlayer("GTL").w(
            "f 1"
        ).wire()
        self.pads[3].setname("DET").w("o f 2").wire()
        self.pads[4].setname("SDA").w("o f 2").wire()
        g = [self.s(nm) for nm in ("SCL", "DET", "SDA")]
        extend2(g)
        return self.board.enriver90(g, -90).wire()


class SMD_3225_4P(Part):
    family = "Y"

    def place(self, dc):
        self.chamfered(dc, 2.8, 3.5, idoffset=(1.4, 0.2))

        for _ in range(2):
            dc.push()
            dc.goxy(-1.75 / 2, 2.20 / 2).right(180)
            self.train(dc, 2, lambda: self.rpad(dc, 1.2, 0.95), 2.20)
            dc.pop()
            dc.right(180)
        [p.setname(nm) for p, nm in zip(self.pads, ["", "GND", "CLK", "VDD"])]


class Osc_6MHz(SMD_3225_4P):
    source = {"LCSC": "C387333"}
    mfr = "S3D6.000000B20F30T"

    def escape(self):
        self.s("GND").w("i -")
        self.s("VDD").w("i +")
        return self.s("CLK")
