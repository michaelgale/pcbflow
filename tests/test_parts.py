import os
import pytest

from pcbflow import *


def test_add_part():
    brd = Board()
    with pytest.raises(NotImplementedError):
        p0 = PCBPart(brd.DC((5, 5)))
    # add with XY tuple
    brd.add_part((1, 2), SOT23, side="top")
    # add with DC
    brd.add_part(brd.DC((5, 6)).right(90), SOIC8, side="bottom")
    assert len(brd.parts) == 2


def test_pinheaders():
    brd = Board()
    with pytest.raises(ValueError):
        PTH(brd.DC((5, 5)))

    with pytest.raises(NotImplementedError):
        PTH(brd.DC((5, 5)), diameter=1.0)

    p0 = SIL(brd.DC((5, 5)), val=7)
    assert p0.N == 7
    assert p0.diameter == 0.8
    assert p0.pitch == INCHES(0.1)

    p0 = SIL(brd.DC((5, 5)), val=8)
    assert p0.N == 8
    assert p0.diameter == 0.8
    assert p0.pitch == INCHES(0.1)

    p0 = SIL_2mm(brd.DC((5, 5)), val=6)
    assert p0.N == 6
    assert p0.diameter == 0.64
    assert p0.pitch == 2.0

    with pytest.raises(ValueError):
        DIP(brd.DC((7, 7)))

    p0 = DIP(brd.DC((7, 7)), val=8)
    assert p0.N == 8
    assert p0.diameter == 0.8
    assert p0.pitch == INCHES(0.1)

    p0 = DIP14(brd.DC((8, 8)))
    assert p0.N == 14
    assert p0.diameter == 0.8
    assert p0.pitch == INCHES(0.1)
