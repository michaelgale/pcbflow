import math

from pcbflow import *


if __name__ == "__main__":
    brd = Board((40, 30))
    brd.DC((10, 10)).text("Top Text", side="top")
    brd.DC((30, 10)).text("Bottom Text", side="bottom")
    brd.add_text((10, 15), "Test Text 1", scale=1.0, layer="GTO")
    brd.add_text((10, 20), "Copper Text 1", scale=1.0, layer="GTL")
    brd.add_text((10, 25), "Copper Text 2", scale=2.0, layer="GTL", keepout_box=True)
    brd.add_text((20, 10), "Copper Text 3", side="bottom", scale=2.0, layer="GBL")
    brd.add_text(
        (20, 15),
        "Copper Text 4",
        side="bottom",
        scale=2.0,
        layer="GBL",
        keepout_box=True,
    )
    brd.add_text(
        (20, 25),
        "Copper Text 5",
        side="bottom",
        scale=2.0,
        layer="GBL",
        keepout_box=True,
        soldermask_box=True,
    )
    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.save("%s" % (os.path.basename(__file__)[:-3]))
