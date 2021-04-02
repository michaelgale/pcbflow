import math
import pcbflow as cu

from pcbflow import mil


if __name__ == "__main__":
    brd = cu.Board(
        (40, 30),
        trace = 0.2,
        space = mil(8),
        via_hole = 0.5,
        via = 1.0,
        via_space = cu.mil(8),
        silk = cu.mil(6))
    brd.via_track_width = cu.mil(24)
    holexy = [
        (5, 5), (5, 25), (35, 5), (35, 25),
    ]
    for x,y in holexy:
        brd.hole((x, y), 2.6, 5)

    brd.DC((10, 10)).rect(3, 3).w("r 90 f 5 l 45 f 5 r 45 f 5").wire(width=mil(32)).via().fan(8, 'GBL')
    cu.C0603(brd.DC((20, 20)).right(90), '0.1 uF', side="bottom")
    cu.C0603(brd.DC((22, 20)).right(90), '0.1 uF')
    cu.C0603(brd.DC((24, 20)).right(90), '0.1 uF').escape("GTL", "GTL")
    cu.R1206(brd.DC((26, 20)).right(90), '1k', side="bottom").escape("GBL", "GBL")
    cu.R1206(brd.DC((28, 10)).right(90), '1k')
    brd.outline()
    brd.fill_any("GTL", "VCC")
    brd.fill_any("GBL", "GL2")
    brd.save("blank")
