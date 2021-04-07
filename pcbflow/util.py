#! /usr/bin/env python3
#
# Misc utility functions
#

import decimal


def better_float(x, tolerance=6):
    ns = str(
        decimal.Decimal(str(x).strip()).quantize(decimal.Decimal(10) ** -tolerance)
    )
    return float(ns)


def better_coords(coords):
    return coords
    nc = []
    for c in coords:
        nc.append((better_float(c[0]), better_float(c[1])))
    return nc
