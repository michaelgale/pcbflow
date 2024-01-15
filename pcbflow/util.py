#! /usr/bin/env python3
#
# Misc utility functions
#

import os
import decimal

REFDES_DICT = {
    "U": "BGA FBGA TFBGA UFBGA WLP XBGA XFBGA Xilinx LFCSP ST_WLCSP WLCSP DFN HVQFN \
          MLF QFN ST_UFQFPN ST_UQFN TDFN TQFN UDFN UFQFPN UQFN VDFN VQFN WDFN WQFN \
          DIP SMDIP PLCC LGA EQFP HTQFP LQFP MQFP PQFP TQFP VQFP HSOP HTSOP HTSSOP \
          HVSSOP MFSOP6 MSOP PSOP QSOP SC SO SOIC SOJ SOP SSO SSOP TSOP TSSOP VSO \
          VSSOP HVSON USON VSON VSONP WSON X2SON TSOC SC SOT SuperSOT TDSON TO \
          TSOT SIPAK",
    "B": "BatteryHolder Battery",
    "C": "CP C Capacitor",
    "D": "D Diode LED HDSP DA04 DA56 DE113 DE114 DE122 DE170 CC56 KCSC02 LTC SA15 \
          OLED LCD HDSM EA CR2013",
    "F": "Fuse Fuseholder",
    "K": "Relay",
    "L": "L Inductor",
    "P": "Pin",
    "R": "R Resistor Potentiometer Varistor",
    "S": "SW ",
    "J": "Connector PinHeader Banana RJ45 RJ12 RJ14 USB TerminalBlock Molex JST \
          Harwin Hirose IDC JAE FFC FPC HDMI DIN Dsub Coaxial BarrelJack Jack",
    "T": "Transformer Pulse Autotransformer ",
    "Y": "Crystal Oscillator",
}


def infer_family(x):
    # look for the first element separated with an underscore
    # as is common with KiCad footprints
    fp = x.split("_")
    if len(fp) > 1:
        fp0 = fp[0].split("-")
        if len(fp0) > 1:
            x = fp0[0]
        else:
            x = fp[0]
    # else look for the first dash separated element common with Eagle libraries
    else:
        fp0 = x.split("-")
        if len(fp0) > 1:
            x = fp0[0]

    for k, v in REFDES_DICT.items():
        if x in v:
            return k
    return ""


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
    max_width += 1
    col_width = int(sz.columns / max_width)
    s = []
    for i, e in enumerate(items, 1):
        s.append(e.ljust(max_width))
        if i % col_width == 0:
            cs.append("%s\n" % ("".join(s)))
            s = []
    cs.append("".join(s))
    return "".join(cs)


def pad_bound(pad):
    minx = pad.xy[0] - pad.pw / 2
    maxx = pad.xy[0] + pad.pw / 2
    miny = pad.xy[1] - pad.h / 2
    maxy = pad.xy[1] + pad.h / 2
    return (minx, miny, maxx, maxy)


def max_bounds(bounds, min_bound=5):
    mbounds = [1e18, 1e18, -1e18, -1e18]
    for b in bounds:
        if len(b) > 0:
            mbounds[0] = min(mbounds[0], b[0])
            mbounds[1] = min(mbounds[1], b[1])
            mbounds[2] = max(mbounds[2], b[2])
            mbounds[3] = max(mbounds[3], b[3])
    # if no valid baounds, return a safe minimum rectangle
    if mbounds[0] > mbounds[2]:
        return (-min_bound, -min_bound, min_bound, min_bound)
    # apply a small boundary margin
    mbounds = [
        mbounds[0] - min_bound,
        mbounds[1] - min_bound,
        mbounds[2] + min_bound,
        mbounds[3] + min_bound,
    ]
    return mbounds


def full_path(file):
    """Returns the fully expanded path of a file"""
    if "~" in str(file):
        return os.path.expanduser(file)
    return os.path.expanduser(os.path.abspath(file))
