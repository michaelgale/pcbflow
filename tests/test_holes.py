import os

from pcbflow import *


def test_add_hole():
    brd = Board()
    n0 = len(brd.npth)
    brd.add_hole((7, 10), 0.5)
    n1 = len(brd.npth)
    assert n1 - n0 == 1
    assert n1 == 1

    brd.add_hole((12, 10), 0.5)
    n2 = len(brd.npth)
    assert n2 == 1

    assert 0.5 in brd.npth
    hl = brd.npth[0.5]
    assert len(hl) == 2
    assert (12, 10) in hl


def test_add_drill():
    brd = Board()
    n0 = len(brd.holes)
    brd.add_drill((3, 4), 0.8)
    n1 = len(brd.holes)
    assert n1 - n0 == 1
    assert n1 == 1

    brd.add_drill((6, 12), 0.8)
    n2 = len(brd.holes)
    assert n2 == 1

    assert 0.8 in brd.holes
    hl = brd.holes[0.8]
    assert len(hl) == 2
    assert (3, 4) in hl


def test_add_hole_drc_nomask():
    brd = Board()
    brd.drc.mask_holes = False

    n0 = len(brd.npth)
    p0 = len(brd.layers["GTS"].polys)
    k0 = len(brd.keepouts)
    brd.add_hole((7, 10), 0.5)
    n1 = len(brd.npth)
    p1 = len(brd.layers["GTS"].polys)
    k1 = len(brd.keepouts)
    assert n1 - n0 == 1
    assert n1 == 1
    assert p1 - p0 == 0
    assert p1 == 0
    assert k1 - k0 == 1
    assert k1 == 1


def test_add_hole_drc_masked():
    brd = Board()
    brd.drc.mask_holes = True
    brd.drc.hole_mask = 0.1
    brd.drc.hole_clearance = 0.15

    n0 = len(brd.npth)
    p0 = len(brd.layers["GTS"].polys)
    q0 = len(brd.layers["GBS"].polys)
    k0 = len(brd.keepouts)
    brd.add_hole((7, 10), 0.5)
    n1 = len(brd.npth)
    p1 = len(brd.layers["GTS"].polys)
    q1 = len(brd.layers["GBS"].polys)
    k1 = len(brd.keepouts)
    assert n1 - n0 == 1
    assert n1 == 1
    assert p1 - p0 == 1
    assert p1 == 1
    assert q1 - q0 == 1
    assert q1 == 1
    assert k1 - k0 == 1
    assert k1 == 1

    kb = brd.keepouts[0].bounds
    assert kb == (6.6, 9.6, 7.4, 10.4)

    mb = brd.layers["GTS"].polys[0][1].bounds
    assert mb == (6.65, 9.65, 7.35, 10.35)

    bb = brd.layers["GBS"].polys[0][1].bounds
    assert bb == (6.65, 9.65, 7.35, 10.35)
