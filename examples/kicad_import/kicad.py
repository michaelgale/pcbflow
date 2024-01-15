import math
import os
import shapely.geometry as sg

from pcbflow import *


if __name__ == "__main__":
    brd = Board((50, 30))
    brd.add_part((5, 8), KiCadPart, libraryfile="kc1.kicad_mod", side="top")
    KiCadPart(brd.DC((22, 20)), libraryfile="kc2.kicad_mod", side="top")
    KiCadPart(brd.DC((8, 22)), libraryfile="kc5.kicad_mod", side="top")
    KiCadPart(brd.DC((35, 20)), libraryfile="kc6.kicad_mod", side="top")
    KiCadPart(brd.DC((25, 20)), libraryfile="kc3.kicad_mod", side="bottom")
    KiCadPart(brd.DC((35, 8)), libraryfile="kc4.kicad_mod", side="bottom")
    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "VCC")

    brd.save("%s" % (os.path.basename(__file__)[:-3]))

    print(brd.parts_str())
    print(brd.layer_net_str())
