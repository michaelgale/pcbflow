"""pcbflow - A python library for PCB layout."""

import os

# fmt: off
__project__ = 'pcbflow'
__version__ = '0.1.0'
# fmt: on

VERSION = __project__ + "-" + __version__

script_dir = os.path.dirname(__file__)


def INCHES(x):
    return x * 25.4


def MILS(x):
    return INCHES(x / 1000)


def MICRONS(x):
    return x / 1000


def DEGREES(r):
    return 180 * r / math.pi


from .util import better_float, better_coords, col_print, col_str
from .gerber import Gerber
from .excellon import excellon
from .hershey import text, ltext, ctext
from .drc import DRC
from .part import Part, pretty_parts
from .footprints import *
from .eagle import EaglePart, list_lbr_packages, show_lbr_package
from .kicad import KiCadPart
from .layer import Layer, OutlineLayer, DEFAULT_LAYERS, DEFAULT_LAYER_ORDER
from .draw import Turtle, Draw
from .board import Board
from .svgout import svg_write
