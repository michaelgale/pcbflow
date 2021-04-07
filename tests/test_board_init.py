import os

from pcbflow import *


def test_init():
    brd = Board()
    assert brd.size == (80, 50)

    brd = Board(size=(40, 30))
    assert brd.size == (40, 30)


def test_init_layers():
    brd = Board()
    order = 0
    for e in DEFAULT_LAYER_ORDER:
        if not e[1] == "P":
            assert e in brd.layers
            assert brd.layers[e].z_order == order
            order += 1


def test_outline():
    brd = Board(size=(40, 30))
    assert brd.size == (40, 30)
    brd.drc.outline_clearance = 0.3

    assert isinstance(brd.layers["GML"], OutlineLayer)
    assert not type(brd.layers["GML"]) == Layer

    p0 = len(brd.layers["GML"].lines)
    k0 = len(brd.keepouts)
    brd.add_outline()
    p1 = len(brd.layers["GML"].lines)
    k1 = len(brd.keepouts)

    ob = brd.layers["GML"].lines[0].bounds
    assert ob == (0.0, 0.0, 40.0, 30.0)

    kb = brd.keepouts[0].bounds
    assert kb == (-0.3, -0.3, 40.3, 30.3)
