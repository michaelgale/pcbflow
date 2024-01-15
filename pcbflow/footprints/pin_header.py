#! /usr/bin/env python3
#
# Pin header parts
#

from pcbflow import *


class PTH(PCBPart):
    def __init__(self, *args, **kwargs):
        if "diameter" not in kwargs and "diameter" not in self.__dict__:
            raise ValueError(
                "PTH class requires keyword argument diameter be specified"
            )
        if not "val" in self.__dict__:
            if "val" in kwargs:
                self.val = kwargs["val"]
            else:
                self.val = 1
        self.N = self.val
        super().__init__(*args, **kwargs)

    def gh(self, dc):
        dc.pw = self.diameter
        dc.h = self.diameter
        dc.board.add_drill(dc.xy, self.diameter)
        p = dc.copy()
        p.n_agon(self.diameter, 8)
        p.pin_pad()
        p = dc.copy()
        p.part = self.id
        self.pads.append(p)


class SIL(PTH):
    def __init__(self, *args, val=None, pitch=None, **kwargs):
        self.family = "J"
        if val is not None:
            self.val = val
        else:
            self.val = 1
        if pitch is not None:
            self.pitch = pitch
        else:
            self.pitch = INCHES(0.1)
        if "diameter" in kwargs:
            self.diameter = kwargs["diameter"]
        else:
            self.diameter = 0.8
        super().__init__(*args, **kwargs)

    def place(self, dc):
        dc.forward(((self.N - 1) / 2) * self.pitch).left(180)
        self.train(dc, self.N, lambda: self.gh(dc), self.pitch)
        [p.set_name(str(i + 1)) for (i, p) in enumerate(self.pads)]


class SIL_2mm(SIL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, pitch=2.0, diameter=0.64, **kwargs)


class DIP(PTH):
    def __init__(self, *args, val=None, **kwargs):
        self.family = "U"
        if val is not None:
            self.val = val
        else:
            raise ValueError(
                "DIP class requires keyword argument val be specified as the number of pins"
            )
        self.diameter = 0.8
        self.pitch = INCHES(0.1)
        super().__init__(*args, **kwargs)

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
        ii = cu.inches(0.1) / 2
        q = math.sqrt((ii**2) + (ii**2))
        for p in self.pads[:4]:
            p.w("l 45").forward(q).left(45).forward(1)
        for p in self.pads[4:]:
            p.w("r 90 f 1")
        oo = list(sum(zip(self.pads[4:], self.pads[:4]), ()))
        cu.extend2(oo)
        return oo


class DIP8(DIP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, val=8, **kwargs)


class DIP14(DIP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, val=14, **kwargs)


class DIP16(DIP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, val=16, **kwargs)


class DIP18(DIP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, val=18, **kwargs)


class DIP20(DIP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, val=20, **kwargs)
