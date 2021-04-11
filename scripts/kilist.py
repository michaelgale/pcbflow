import math
import os
import sys
import argparse
import glob
import crayons
import skidl
from skidl import footprint_search_paths

skidl.logger.stop_file_output()
skidl.erc_logger.stop_file_output()


from pcbflow import *

FP_LIB_PATH = None
SYM_LIB_PATH = None


def file_search(files):
    file_list = []
    for f in files:
        _, fn = os.path.split(full_path(f))
        nterms = len(argsd["searchspec"])
        if nterms > 0:
            term_count = 0
            terms = []
            for term in argsd["searchspec"]:
                if argsd["ignore_case"]:
                    terms.append(term.lower())
                else:
                    terms.append(term)
            for term in terms:
                if argsd["ignore_case"]:
                    if term in fn.lower():
                        term_count += 1
                else:
                    if term in fn:
                        term_count += 1
            if term_count == nterms:
                file_list.append(fn)
        else:
            file_list.append(fn)
    return file_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "searchspec", nargs="*", default=None, help="Optional search terms"
    )
    parser.add_argument(
        "-c",
        "--ignore_case",
        action="store_true",
        default=False,
        help="Case insensitive search",
    )
    parser.add_argument(
        "-f",
        "--footprints",
        action="store_true",
        default=False,
        help="Search footprints library",
    )
    parser.add_argument(
        "-s",
        "--symbols",
        action="store_true",
        default=False,
        help="Search symbols library",
    )
    args = parser.parse_args()
    argsd = vars(args)

    if len(sys.argv) == 1:
        parser.print_help()

    for path in skidl.footprint_search_paths["kicad"]:
        kicadfn = path + os.sep + "kicad_common"
        if os.path.isfile(full_path(kicadfn)):
            with open(kicadfn, "r") as f:
                kf = f.readlines()
            for line in kf:
                ls = line.split("=")
                if ls[0] == "KISYSMOD":
                    FP_LIB_PATH = ls[1].rstrip()
                if ls[0] == "KICAD_SYMBOL_DIR":
                    SYM_LIB_PATH = ls[1].rstrip()
            if FP_LIB_PATH is None:
                print(crayons.red("Unable to KiCAD footprints directory"))
            if SYM_LIB_PATH is None:
                print(crayons.red("Unable to KiCAD symbols directory"))
    if argsd["footprints"]:
        print(crayons.cyan("Searching for footprints in %s..." % (FP_LIB_PATH)))
        ALL_KICAD_FILES = glob.glob(
            FP_LIB_PATH + os.sep + "**/*.kicad_mod", recursive=True
        )
        file_list = file_search(ALL_KICAD_FILES)
        col_print(file_list)
        print(crayons.green("%d footprint module files found" % (len(file_list))))

    if argsd["symbols"]:
        print(crayons.cyan("Searching for symbols libraries in %s..." % (SYM_LIB_PATH)))
        ALL_KICAD_FILES = glob.glob(SYM_LIB_PATH + os.sep + "**/*", recursive=True)
        file_list = file_search(ALL_KICAD_FILES)
        col_print(file_list)
        print(crayons.green("%d symbol files found" % (len(file_list))))
