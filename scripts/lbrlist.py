import math
import argparse
import shapely.geometry as sg

try:
    import crayons
except:
    pass

from pcbflow import *

SVG_BOUNDARY = 5


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "library", metavar="library", type=str, help="EAGLE Library file"
    )
    parser.add_argument(
        "-p", "--part", action="store", default=None, help="Select a part from library"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Show verbose entities of part",
    )
    parser.add_argument(
        "-s",
        "--svg",
        action="store_true",
        default=False,
        help="Export part to SVG file",
    )
    args = parser.parse_args()
    argsd = vars(args)

    if argsd["part"] is not None:
        part = argsd["part"].upper()
        show_lbr_package(argsd["library"], part)
        brd = Board((100, 100))
        brd.drc.mask_holes = True
        brd.drc.hole_mask = MILS(10)
        try:
            ep = EaglePart(
                brd.DC((50, 50)),
                libraryfile=argsd["library"],
                partname=part,
                debug=argsd["verbose"],
            )
        except ValueError:
            print(
                crayons.red("Part ")
                + part
                + crayons.red(" was not found in ")
                + argsd["library"]
            )
            exit()
        if argsd["svg"]:
            print("Exporting %s in %s..." % (part, argsd["library"]))
            b = []
            for layer in ["GTO", "GTL", "GTS", "GTP"]:
                obj = brd.layers[layer].preview()
                b.append(obj.bounds)
            bounds = max_bounds(b, min_bound=SVG_BOUNDARY)
            g = sg.box(*bounds)
            brd.layers["GML"].add(g)
            svg_write(brd, part + ".svg")
            print(crayons.green("%s exported to %s.svg" % (part, part)))
    else:
        print(
            "Package list of Eagle library " + crayons.green("%s:" % (argsd["library"]))
        )
        n = list_lbr_packages(argsd["library"])
        print(crayons.green("%d packages found in %s" % (n, argsd["library"])))
