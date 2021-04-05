
#! /usr/bin/env python3
#
# Pin header parts
#

from pcbflow import *


class PTH(Part):
    r = 0.8

    def gh(self, dc):
        dc.board.add_drill(dc.xy, self.r)
        p = dc.copy()
        p.n_agon(self.r, 8)
        p.contact()

        p = dc.copy()
        p.part = self.id
        self.pads.append(p)

class SIL(PTH):
    family  = "J"
    pitch = INCHES(0.1)
    def place(self, dc):
        self.N = int(self.val)
        # self.chamfered(dc, T + 2, T * self.N + 2)
        dc.forward(((self.N - 1) / 2) * self.pitch).left(180)
        self.train(dc, self.N, lambda: self.gh(dc), self.pitch)
        [p.setname(str(i + 1)) for (i, p) in enumerate(self.pads)]


class SIL_2mm(SIL):
    r = 0.64
    pitch = 2.0


class DIP(PTH):
    family = "U"
    pitch = INCHES(0.1)
    def place(self, dc):
        pn = (self.N // 4 - 1) + 0.5
        self.chamfered(dc, 6.2, (self.N // 2 * self.pitch) + 0.2)
        for _ in range(2):
            dc.push()
            dc.goxy(-1.5 * self.pitch, pn * self.pitch).left(180)
            self.train(dc, self.N // 2, lambda: self.gh(dc), self.pitch)
            dc.pop()
            dc.right(180)

    def escape(self):
        ii = cu.inches(.1) / 2
        q = math.sqrt((ii ** 2) + (ii ** 2))
        for p in self.pads[:4]:
            p.w("l 45").forward(q).left(45).forward(1)
        for p in self.pads[4:]:
            p.w("r 90 f 1")
        oo = list(sum(zip(self.pads[4:], self.pads[:4]), ()))
        cu.extend2(oo)
        return oo

class DIP8(DIP):
    N = 8

class DIP14(DIP):
    N = 14

class DIP16(DIP):
    N = 16

class DIP18(DIP):
    N = 18

class DIP20(DIP):
    N = 20      