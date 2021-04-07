import os
import pytest

from pcbflow import *


def test_add_smd_discrete():
    brd = Board()

    p0 = C0402(brd.DC((5, 5)), val="0.1u")
    assert p0.val == "0.1u"
    assert p0.family == "C"

    p0 = C0603(brd.DC((5, 5)), val="0.1u")
    assert p0.val == "0.1u"
    assert p0.family == "C"

    p0 = C0805(brd.DC((5, 5)), val="0.1u")
    assert p0.val == "0.1u"
    assert p0.family == "C"

    p0 = C1206(brd.DC((5, 5)), val="0.1u")
    assert p0.val == "0.1u"
    assert p0.family == "C"

    p0 = R0402(brd.DC((5, 5)), val="1k")
    assert p0.val == "1k"
    assert p0.family == "R"

    p0 = R0603(brd.DC((5, 5)), val="470")
    assert p0.val == "470"
    assert p0.family == "R"

    p0 = R0805(brd.DC((5, 5)), val="330")
    assert p0.val == "330"
    assert p0.family == "R"

    p0 = R1206(brd.DC((5, 5)), val="560")
    assert p0.val == "560"
    assert p0.family == "R"
