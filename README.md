| | | |
| --- | --- | --- |
| <img src=./images/sample_top.png> | <img src=./images/sample_bot.png> | <img src=./images/sample_all.png> |

# pcbflow - Python PCB layout and design (based on CuFlow)

![python version](https://img.shields.io/static/v1?label=python&message=3.9%2B&color=blue&style=flat&logo=python)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>  

![https://travis-ci.org/michaelgale/pcbflow](https://travis-ci.com/michaelgale/pcbflow.svg?branch=main)
[![codecov](https://codecov.io/gh/michaelgale/pcbflow/branch/main/graph/badge.svg)](https://codecov.io/gh/michaelgale/pcbflow)
![https://github.com/michaelgale/pcbflow/issues](https://img.shields.io/github/issues/michaelgale/pcbflow.svg?style=flat)


This repository contains a python based Printed Circuit Board (PCB) layout and design package based on [CuFlow](https://github.com/jamesbowman/cuflow) by James Bowman.

This implementation is an experimental variation of CuFlow.  It attempts to modularize the components of CuFlow and extend/modify its functionality in some key areas:

- allow component placement on top or bottom (automatically chooses top or bottom companion layers of silkscreen, soldermask, copper)
- allow customization of track widths, drill/hole types
- contain design rules in a class rather than the Board class
- improve layout metrics
- robust import of components from Eagle LBR and KiCAD mod files
- enhanced Gerber files with FileFunction assignments
- more export formats including stylized views for SVG, PNG, PDF
- integration with [SKiDL](https://github.com/xesscorp/skidl) for complete scripted EDA workflow

This implementation is alpha and not fully documented.

## Requirements

Since the initial release of `pcbflow`, some changes have been made to adapt with newer versions of python and library dependancies.  In particular:

- the initial versions of `pcbflow` used `shapely` v.1.6+. However `shapely` has changed the way geometries are iterated in v.2.0.1+; therefore `pcbflow` has been changed to support `shapley` versions 2.0.1+

>
> `pcbflow` has been changed to support `shapley` versions 2.0.1+ ONLY.
>  Check your version with `pip list` and verify `shapley` is v.2.0.1+
> 

## Installation

The **pcbflow** package can be installed directly from the source code:

```bash
  $ git clone https://github.com/michaelgale/pcbflow.git
  $ cd pcbflow
  $ pip install .
```

## Basic Usage

After installation, the package can imported:

```shell
    $ python
    >>> import pcbflow
    >>> pcbflow.__version__
```

An example of the package can be seen below

```python

from pcbflow import *

# create a 40 mm x 30 mm PCB with outline
brd = Board((40, 30))
brd.add_outline()
# fill the top and bottom copper layers and merge nets named "GND"
brd.fill_layer("GTL", "GND")
brd.fill_layer("GBL", "GND")
# save the PCB asset files
brd.save("mypcb")
```

## Board Object

The `Board` class is a top level object used to perform all the tasks to build a scripted PCB design in python.  Once an instance of `Board` is created, calling methods to add features and configure the PCB can then be peformed as desired.

## PCB Layers

**pcbflow** creates the following layer stack by default:

- `GML` - Mechanical outline
- `GTD` - Top side documentation
- `GTP` - Top side solder paste
- `GTO` - Top side silkscreen
- `GTS` - Top side solder mask
- `GTL` - Top side copper
- `GBL` - Bottom side copper
- `GBS` - Bottom side solder mask
- `GBO` - Bottom side silkscreen
- `GBP` - Bottom side solder paste
- `GBD` - Bottom side documentation

Additional internal copper layers can be added as follows:

```python
  brd.add_inner_copper_layer(layer_count=1)
```

This will insert a copper layer named `GP2` inbetween `GTL` and `GBL`.  Subsequent addition of copper layers will be named `GP3`, `GP4`, etc.  `layer_count` specifies how many inner copper layers to add.

## Design Rules

A basic set of design rules is stored in the `Board.drc` attribute.  It has the following attributes:

```python
# Copper features
self.trace_width = MILS(8)
self.via_drill = 0.5
self.via_annular_ring = MILS(8)
self.via_track_width = MILS(16)
# Clearances
self.clearance = MILS(8)
self.outline_clearance = MILS(20)
self.hole_clearance = MILS(20)
# Soldermask
self.mask_vias = False
self.mask_holes = True
self.hole_mask = MILS(16)
self.soldermask_margin = MILS(3)
# Other
self.bitmap_res = 0.04
self.silk_width = MILS(6)
self.text_silk_width = MILS(6)
```

## Numeric Values

The default internal representation of numerical values of distance, length, etc. is metric millimetres (mm).  However, **pcbflow** has the following convenience functions to specify values in other units:

- `MILS(x)` - thousandths of an inch
- `INCHES(x)` - inches
- `MICRONS(x)` - micrometres

## Holes

You can add standard non-plated through holes as follows:

```python
brd.add_hole((x, y), diameter)
```

Note that added holes will automatically add a keepout and solder mask margin if specified by the `DRC`.  `DRC.hole_clearance` specifies the keepout border clearance, `DRC.mask_holes` enables/disables a solder mask region over the hole with a border width specified by `DRC.hole_mask`.

To add a plated through hole:

```python
brd.add_drill((x, y), diameter)
```

## Text

Text annotations can be applied to any layer as follows:

```python
brd.add_text((x, y), "ABC",
      scale=1.0,
      angle=0.0,
      side="top",
      layer=None,
      keepout_box=False,
      soldermask_box=False,
      justify="centre")
```

The `side` argument can be specified as either `top` or `bottom`.  This will mirror the text for bottom layers so that it is the correct orientation for fabrication.

`keepout_box` specifies whether a keepout border region be applied to the text to prevent it from be lost in a poured copper layer for example.

`soldermask_box` specifies whether a solder mask region be applied so that the text would appear unmasked.

## Bitmaps

Arbitrary bitmap logos/annotations can be applied to the PCB as follows:

```python
brd.add_bitmap((x, y), "logo.png", 
  scale=None,
  side="top",
  layer=None,
  keepout_box=False,
  soldermask_box=False)
```

The bitmap should be a monochrome bitmap image with transparent background.  It will be automatically converted into polygons and added to the desired `layer`.  The bitmap size is can be adjusted with the `scale` parameter.  Furthermore, `keepout_box` and `soldermask_box` can be applied as desired.  Lastly, the `side` parameter can flip the orientation of the bitmap for bottom side layers if set to `bottom`

## Named Polygons

Arbitary polygon regions can be added to a copper layer with a name corresponding to its net name.  For example, this can be used to apply different voltage "patches" under a part requiring several voltages, or to make a split plane of several voltages or GND references. 

```python
# add a polygon with a coordinate list
#   add_named_poly(coords, layer, name)
brd.add_named_poly([(1,1), (1,2), (5,1)], layer="GTL", "GND")

# convenience method for making a rectangular polygon with two corner points
#   add_named_rect(top_left, bottom_right, layer, name)
brd.add_named_rect((1, 10), (20, 3), "GBL", "VCC")
```

## Parts

Parts can be added in four ways:

1. Drawing directly with primitives in class derived from `PCBPart` (see the `footprints` folder for examples)
2. Importing a package from an Eagle library file using `EaglePart`
3. Importing a footprint from a KiCAD footprint library file using `KiCadPart`
4. Instantiating a part from a SKiDL circuit using `SkiPart`

```python
# adding a generic part with SOT23(Part)
brd.add_part((10, 20), SOT23, side="top")
# adding a generic R0603(PCBPart) SMD resistor by passing the board "Drawing Context" (DC)
#   PCBPart classes instantiate themselves directly from DC--this allows the part
#   to derive its location, orientation, etc.
R0603(brd.DC((20, 10)), "4.7k", side="bottom")
# this is also equivalent:
brd.add_part((20, 10), R0603, val="4.7k", side="bottom")

# We can add multiple parts with an iterator:
for x in range(5):
    brd.add_part((5 + x*3, 4), C0402, val="0.1u", side="top")

# adding an Eagle part called USB-B-SMT from sparkfun.lbr
# chaining the right(90) method to DC places the part 90 deg rotated
EaglePart(brd.DC((10, 10)).right(90), libraryfile="sparkfun.lbr", partname="USB-B-SMT", side="top")
# this is also equivalent:
brd.add_part((10, 10), EaglePart, libraryfile="sparkfun.lbr", partname="USB-B-SMT", side="top", rot=90)

# adding a KiCAD footprint part from file kc1.kicad_mod
# specifying the side="bottom" automatically maps the footprint copper, mask, paste,
# and silkscreen layers to the bottom (automatically mirroring in the horizontal axis)
KiCadPart(brd.DC((10, 10)), libraryfile="kc1.kicad_mod", side="bottom")
# this is also equivalent:
brd.add_part((10, 10), KiCadPart, libraryfile="kc1.kicad_mod", side="bottom")

# assigning a variable to a placed part allow us to reference it again
# later for tasks such as renaming pads, routing signals from a pad location,
# routing a group of signals as a bus (or "river" in CuFlow), etc.
usb_con = EaglePart(brd.DC((10, 10)), libraryfile="sparkfun.lbr", partname="USB-B-SMT", side="top")
# route a wire from pad 3 to 5 mm right, 10 mm up with a width 0.25 mm
# if width is omitted it will use the default trace_width in Board.DRC
usb_con.pads[3].w("r 90 f 5 l 90 f 10").wire(width=0.25)

# print a PCBPart's details (pad 3 happens to be the USB connector's D- line)
print(usb_con)
# Part: 3   top    ( 10.00,  10.00) / 0 deg  6 pads
#   0: 5 (10.58, 16.80)    1: 6 (10.58, 3.20)     2: D+ (17.00, 11.88)   3: D- (22.00, 20.62)   4: GND (17.00, 9.38)
#   5: VUSB (17.00, 8.12)

# alternatively, we can reference the pad by name to do the same thing
usb_con.pad("D-").turtle("r 90 f 5 l 90 f 10").wire(width=0.25)     
```

## Saving Asset Files

**pcbflow** can generate a variety of output asset files representing the PCB.  These include:

- Gerber files for fabrication
- Bill of Materials (BOM) CSV file
- Centroids of parts CSV file
- SVG preview renders of the top, bottom, or all layer views
- Postscript preview render
- Povray raytracing files

Outfiles can be created in the same folder as the script file or in a subfolder under the script (generated automatically). To generate asset files:

```python
brd.save(basename, in_subdir=True, 
  gerber=True, pdf=True, bom=True, centroids=True, povray=False)
```

The `in_subdir` argument specifies whether a subfolder named `basename` should be created for the assets.
The `gerber`, `pdf`, `bom`, `centroids`, `povray` arguments specify which of the asset types to generate.

Alternatively, individual asset types can be generated using these convenience methods:

```python
brd.save_gerbers(basename, in_subdir=True)
brd.save_pdf(basename, in_subdir=True)
brd.save_png(basename, in_subdir=True)
brd.save_svg(basename, in_subdir=True)
brd.save_centroids(basename, in_subdir=True)
brd.save_bom(basename, in_subdir=True)
```

## Putting it Together with SKiDL

**pcbflow** is best used as a companion to [SKiDL](https://github.com/xesscorp/skidl).  SKiDL is a python based tool which allows you to script the design of electronic circuits.  SKiDL integrates with KiCAD symbol and footprint libraries to enable seamless building of circuits with a rich library of pre-built parts.

After a circuit has been designed and validated with SKiDL, **pcbflow** can then be used to physically render the circuit on to a PCB.  The attributes of the PCB including its size, shape, layer stack-up, as well as some basic design rules can be customized as desired with python code.  A typical workflow will consist of the following steps:

1. Generally, a script file will start with a SKiDL circuit definition. This will consist of various `Part` and `Net` declarations followed by code which makes net connections among parts.
2. Next, a **pcbflow** `Board` instance can be declared and various `Board` methods can be used to configure the basic attributes of the PCB such as its size, layers, etc.
3. Parts declared in SKiDL can then be placed on the PCB.  This consists of accessing SKiDL parts either by iterating through the `default_circuit.parts` attribute or iterating over `Part` assignments explictly made in the code (e.g. `mcu = Part("DSP_Microchip_DSPIC33", "DSPIC33EP256MU806-xPT", footprint="TQFP-64_10x10mm_P0.5mm",)`)
4. Each part will require the instantiation of a `SkiPart(brd.DC(x, y), part, side=side)` object.  This explictly tells **pcbflow** where the part should physically be placed on the PCB with its `x`, `y` coordinates and on which side of the PCB it is placed (`"top"` or `"bottom"`).  The `SkiPart` object initialization can be passed a native SKiDL `Part` instance in order to derive the physical footprint, reference designator, family, etc.
5. After parts have been placed, network connections can then be made using a combination of **pcbflow** operations including:
    - "fanout" pads to named vias
    - adding named polygons which can absorb a via connection or part pad of the same net name
    - "turtle" style routing commands to physically describe a net route path
6. Special PCB features such as "keepout" regions, text annotations, bitmap logos, mounting holes, etc. can be added to the PCB as desired.
7. If any layers are desired to be "flooded" with a named signal (e.g. a GND fill), then the `Board.fill_layer()` method can be called on any of the PCB layers as required.
8. Lastly, the rendered PCB can be saved to a variety of asset files as desired including:
   - Gerber files for fabrication
   - BOM and centroid placement CSV files
   - PDF, SVG, PNG preview files for iterative checking of the board appearance or documentation

An example script is shown below:

```python
import os
import math
import glob
import shapely.geometry as sg

from pcbflow import *
from skidl import *


if __name__ == "__main__":
    ###
    ### SKiDL Circuit Declarations
    ###

    # Declare microcontroller
    mcu = Part(
        "DSP_Microchip_DSPIC33",
        "DSPIC33EP256MU806-xPT",
        footprint="TQFP-64_10x10mm_P0.5mm",
    )
    # Declare a generic 0603 capacitor
    cap = Part(
        "Device",
        "C",
        footprint="C_0603_1608Metric_Pad1.08x0.95mm_HandSolder",
        dest=TEMPLATE,
    )
    # Declare 3 instances of our generic capacitor with values
    c1 = cap(value="10uF")
    c2 = cap(value="0.1uF")
    c3 = cap(value="0.1uF")

    # Create GND and VDD nets
    vdd = Net("VDD")
    gnd = Net("GND")

    # Assign VDD and GND to our parts
    mcu["VDD"] += vdd
    mcu["VSS"] += gnd
    for c in [c1, c2, c3]:
        c[1] += vdd
        c[2] += gnd

    ###
    ### pcbflow PCB Declarations
    ###

    # Create a pcbflow Board instance
    brd = Board((55, 30))
    
    # add two inner copper layers (named GP2, GP3)
    brd.add_inner_copper_layer(2)
    # Place 2 mm mounting holes in the corners
    holes = ((5, 5), (5, 25), (50, 5), (50, 25))
    for hole in holes:
        brd.add_hole(hole, 2.0)
    # Add some text (silkscreen on the top), as copper on the bottom
    brd.add_text((10, 25), "Made with pcbflow", justify="left")
    brd.add_text((10, 25), "Made with pcbflow", layer="GBL", keepout_box=True, justify="left")

    # Place a VDD patch under MCU on layer GP3
    brd.add_named_rect((27, 25), (45, 5), layer="GP3", name="VDD")

    # Assign a convenient reference to the default SKiDL circuit
    ckt = default_circuit

    print("Circuit:  Parts: %d  Nets: %d" % (len(ckt.parts), len(ckt.nets)))

    # Assign part locations (we're adding an extra atrribute to the skidl.Part object)
    mcu.loc = (35, 15)
    c1.loc = (25,15)
    c2.loc = (45,15)
    c3.loc = (37,6.5)
    sides = ["top", "bottom", "top", "bottom"]

    # Instantiate SkiPart(PCBPart) instances
    for part, side in zip(ckt.parts, sides):
        sp = SkiPart(brd.DC(part.loc), part, side=side)
        # "fanout" GND and VDD vias from parts with GND and VDD net connections
        sp.fanout(["VDD"])
        sp.fanout(["GND"], relative_to="inside")

    print(brd.parts_str())
    
    # finish the PCB with an outline and poured copper layers
    brd.add_outline()
    brd.fill_layer("GTL", "GND")
    brd.fill_layer("GBL", "GND")
    brd.fill_layer("GP3", "GND")

    # Save the rendered PCB to asset files 
    brd.save("%s" % (os.path.basename(__file__)[:-3]))
```

| Top | Top Document |
| --- | --- |
| <img src=./images/preview_top.png> | <img src=./images/preview_top_docu.png> |

| Bottom | Bottom Document |
| --- | --- |
| <img src=./images/preview_bot.png> | <img src=./images/preview_bot_docu.png> |

| All |
| --- |
| <img src=./images/preview_all.png> |


## To Do

- Routing and Nets
- DRC checking
- More tests
- CI

## Releases

None yet.

## Authors

**pcbflow** was written by [Michael Gale](https://github.com/michaelgale) and is based on the [CuFlow](https://github.com/jamesbowman/cuflow) package by James Bowman.
