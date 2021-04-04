"""pcbflow - A python library for PCB layout."""

import os

# fmt: off
__project__ = 'pcbflow'
__version__ = '0.1.0'
# fmt: on

VERSION = __project__ + "-" + __version__

script_dir = os.path.dirname(__file__)

def inches(x):  return x * 25.4
def mil(x):     return inches(x / 1000)
def micron(x):  return x / 1000
def DEGREES(r): return 180 * r / math.pi

from .gerber import Gerber
from .excellon import excellon
from .svgout import svg_write
from .hershey import text, ltext, ctext
from .drc import DRC
from .part import *
from .eagle import LibraryPart
from .pcbflow import *
