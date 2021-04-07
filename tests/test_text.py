import os

from pcbflow import *


def test_add_text():
    brd = Board()

    n0 = len(brd.layers["GTO"].polys)
    brd.add_text((5, 3), "ABC")
    n1 = len(brd.layers["GTO"].polys)
    assert n1 - n0 == 1
    assert n1 == 1

    n0 = len(brd.layers["GBO"].polys)
    brd.add_text((5, 3), "ABC", layer="GBO")
    n1 = len(brd.layers["GBO"].polys)
    assert n1 - n0 == 1
    assert n1 == 1


def test_add_text_keepout():
    brd = Board()
    brd.drc.clearance = 0.1

    n0 = len(brd.layers["GTO"].polys)
    k0 = len(brd.layers["GTO"].keepouts)
    brd.add_text((5, 3), "ABC", keepout_box=True)
    n1 = len(brd.layers["GTO"].polys)
    k1 = len(brd.layers["GTO"].keepouts)
    assert n1 - n0 == 1
    assert n1 == 1
    assert k1 - k0 == 1
    assert k1 == 1

    bt = brd.layers["GTO"].polys[0][1].bounds
    bk = brd.layers["GTO"].keepouts[0].bounds

    assert bt[0] - bk[0] - brd.drc.clearance < 1e-3
    assert bt[1] - bk[1] - brd.drc.clearance < 1e-3
    assert bk[2] - bt[2] - brd.drc.clearance < 1e-3
    assert bk[3] - bt[3] - brd.drc.clearance < 1e-3

    n0 = len(brd.layers["GBO"].polys)
    k0 = len(brd.layers["GBO"].keepouts)
    brd.add_text((10, 20), "ABC", layer="GBO", keepout_box=True)
    n1 = len(brd.layers["GBO"].polys)
    k1 = len(brd.layers["GBO"].keepouts)
    assert n1 - n0 == 1
    assert n1 == 1
    assert k1 - k0 == 1
    assert k1 == 1


def test_add_text_masked():
    brd = Board()
    brd.drc.soldermask_margin = 0.12

    n0 = len(brd.layers["GTO"].polys)
    k0 = len(brd.layers["GTS"].polys)
    brd.add_text((5, 3), "ABC", soldermask_box=True)
    n1 = len(brd.layers["GTO"].polys)
    k1 = len(brd.layers["GTS"].polys)
    assert n1 - n0 == 1
    assert n1 == 1
    assert k1 - k0 == 1
    assert k1 == 1

    bt = brd.layers["GTO"].polys[0][1].bounds
    bk = brd.layers["GTS"].polys[0][1].bounds

    assert bt[0] - bk[0] - brd.drc.soldermask_margin < 1e-3
    assert bt[1] - bk[1] - brd.drc.soldermask_margin < 1e-3
    assert bk[2] - bt[2] - brd.drc.soldermask_margin < 1e-3
    assert bk[3] - bt[3] - brd.drc.soldermask_margin < 1e-3

    n0 = len(brd.layers["GBO"].polys)
    k0 = len(brd.layers["GBS"].polys)
    brd.add_text((10, 20), "ABC", side="bottom", layer="GBO", soldermask_box=True)
    n1 = len(brd.layers["GBO"].polys)
    k1 = len(brd.layers["GBS"].polys)
    assert n1 - n0 == 1
    assert n1 == 1
    assert k1 - k0 == 1
    assert k1 == 1
