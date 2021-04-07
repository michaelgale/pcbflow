import os

from pcbflow import *


def test_init_layers():
    brd = Board()
    order = 0
    for e in DEFAULT_LAYER_ORDER:
        if not e[1] == "P":
            assert e in brd.layers
            assert brd.layers[e].z_order == order
            order += 1


def test_add_layer():
    brd = Board()
    n0 = len(brd.layers)
    c0 = brd.get_copper_layers(as_names=True)

    brd.add_inner_copper_layer()
    n1 = len(brd.layers)
    c1 = brd.get_copper_layers(as_names=True)
    assert n1 - n0 == 1
    assert len(c1) - len(c0) == 1


def test_pad_stack_layers():
    brd = Board()
    pl = brd.get_pad_stack_layers(as_names=True)
    assert "GBL" in pl
    assert "GBS" in pl
    assert "GTL" in pl
    assert "GTS" in pl


def test_smd_pad_layers():
    brd = Board()
    pl = brd.get_smd_pad_layers(side="top", as_names=True)
    assert len(pl) == 3
    assert "GTP" in pl
    assert "GTS" in pl
    assert "GTL" in pl

    pl = brd.get_smd_pad_layers(side="bottom", as_names=True)
    assert len(pl) == 3
    assert "GBP" in pl
    assert "GBS" in pl
    assert "GBL" in pl

    pl = brd.get_smd_pad_layers(side="top", as_names=True, ignore_paste=True)
    assert len(pl) == 2
    assert "GTS" in pl
    assert "GTL" in pl


def test_silk_layer():
    brd = Board()
    sl = brd.get_silk_layer(side="top", as_name=True)
    assert sl == "GTO"
    sl = brd.get_silk_layer(side="bottom", as_name=True)
    assert sl == "GBO"
