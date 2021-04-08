#! /usr/bin/env python3
#
# Misc utility functions
#

import os
import decimal


def better_float(x, tolerance=6):
    ns = str(
        decimal.Decimal(str(x).strip()).quantize(decimal.Decimal(10) ** -tolerance)
    )
    return float(ns)


def better_coords(coords):
    nc = []
    for c in coords:
        nc.append((better_float(c[0]), better_float(c[1])))
    return nc


def col_print(items):
    print(col_str(items))


def col_str(items):
    cs = []
    sz = os.get_terminal_size()
    max_width = 0
    for e in items:
        max_width = max(max_width, len(e))
    col_width = int(sz.columns / (max_width + 1))
    s = []
    for i, e in enumerate(items, 1):
        s.append(e.ljust(max_width))
        if i % col_width == 0:
            cs.append("%s\n" % ("".join(s)))
            s = []
    cs.append("%s\n" % ("".join(s)))
    return "".join(cs)
