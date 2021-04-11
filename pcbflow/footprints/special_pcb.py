#! /usr/bin/env python3
#
# Special PCB feature parts
#

from pcbflow import *


class Castellation(PCBPart):
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
            dc.pin_pad()
            dc.push()
            dc.forward(0.375)
            dc.board.add_hole(dc.xy, 0.7)
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
                p.set_name("P" + str(cnt["port"]))

        a = group(self.pads[:gnd], -90)
        b = group(self.pads[gnd + 1 :], 90)
        return (a, b)

    def sidevia(self, dc, dst):
        assert dst in "-+."
        dc.set_width(0.6)
        for l in ("GTL", "GBL"):
            dc.push()
            dc.set_layer(l)
            dc.push()
            dc.w("f -0.3 r 90 f 0.4 " + dst)
            dc.pop()
            dc.w("f -0.3 l 90 f 0.4 " + dst)
            dc.pop()

    def escape1(self):
        pp = self.pads[::-1]
        names = "PGM TDI TDO TCK TMS".split()
        [t.set_name(n) for t, n in zip(pp, names)]

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
            pp[0].push().set_layer(l).set_width(0.6).w(
                "f -0.3 r 90 f 0.5 + f 0.5 +"
            ).pop()
        self.sidevia(pp[1], "-")
        return pp[2]

    def escape3(self):
        pp = self.pads[::-1]
        names = "SDA SCL INT RST".split()
        [t.set_name(n) for t, n in zip(pp, names)]

        for t in pp:
            dc = t.copy().w("i f 0.6")
            (x, y) = dc.xy
            dc.board.layers["GTO"].add(hershey.ctext(x, y, t.name))
            t.w("i f 1").wire("GBL")

        return self.board.enriver(pp, 45).left(45).wire()
