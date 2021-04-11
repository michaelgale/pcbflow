import os

from pcbflow import *


def test_add_named_rect():
    brd = Board()

    p0 = len(brd.layers["GTL"].polys)
    q0 = len(brd.layers["GBL"].polys)
    r0 = len(brd.layers["GTL"].named_polys)
    s0 = len(brd.layers["GBL"].named_polys)
    brd.add_named_rect((5, 20), (20, 15), "GTL", "GND")
    brd.add_named_rect((15, 20), (30, 15), "GBL", "VCC")
    p1 = len(brd.layers["GTL"].polys)
    q1 = len(brd.layers["GBL"].polys)
    r1 = len(brd.layers["GTL"].named_polys)
    s1 = len(brd.layers["GBL"].named_polys)
    assert p1 - p0 == 0
    assert p1 == 0
    assert q1 - q0 == 0
    assert q1 == 0
    assert r1 - r0 == 1
    assert r1 == 1
    assert s1 - s0 == 1
    assert s1 == 1

    mb = brd.layers["GTL"].named_polys[0][1].bounds
    assert mb == (5.0, 15.0, 20.0, 20.0)

    bb = brd.layers["GBL"].named_polys[0][1].bounds
    assert bb == (15.0, 15.0, 30.0, 20.0)


def test_add_named_poly():
    brd = Board()

    p0 = len(brd.layers["GTL"].named_polys)
    coords = [(5, 30), (8, 30), (20, 20), (15, 20), (8, 10), (5, 10)]
    brd.add_named_poly(coords, "GTL", "GND")
    p1 = len(brd.layers["GTL"].named_polys)
    assert p1 - p0 == 1
    assert p1 == 1

    mb = brd.layers["GTL"].named_polys[0][1].bounds
    assert mb == (5.0, 10.0, 20.0, 30.0)
