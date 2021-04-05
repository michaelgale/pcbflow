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


from .gerber import Gerber
from .excellon import excellon
from .svgout import svg_write
from .hershey import text, ltext, ctext
from .drc import DRC
from .part import Part, pretty_parts
from .footprints import *
from .eagle import LibraryPart
from .layer import Layer, OutlineLayer, DEFAULT_LAYERS, DEFAULT_LAYER_ORDER
from .draw import Turtle, Draw, Drawf
from .pcbflow import *
