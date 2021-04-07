# pcbflow - Python PCB layout and design (based on CuFlow)

![python version](https://img.shields.io/static/v1?label=python&message=3.6%2B&color=blue&style=flat&logo=python)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>  

This repository contains a python based Printed Circuit Board (PCB) layout and design package based on [CuFlow](https://github.com/jamesbowman/cuflow) by James Bowman.

This implementation is an experimental variation of CuFlow.  It attempts to modularize the components of CuFlow and extend/modify its functionality in some key areas:

- allow component placement on top or bottom (automatically chooses top or bottom companion layers of silkscreen, soldermask, copper)
- allow customization of track widths, drill/hole types
- contain design rules in a class rather than the Board class
- improve layout metrics
- robust import of components from Eagle LBR files
- enhanced Gerber files with FileFunction assignments
- enhanced SVG export

This implementation is very alpha and not documented.

## Installation

The **pcbflow** package can be installed directly from the source code:

```bash
  $ git clone https://github.com/michaelgale/pcbflow.git
  $ cd pcbflow
  $ python setup.py install
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
- `GTP` - Top side solder paste
- `GTO` - Top side silkscreen
- `GTS` - Top side solder mask
- `GTL` - Top side copper
- `GBL` - Bottom side copper
- `GBS` - Bottom side solder mask
- `GBO` - Bottom side silkscreen
- `GBP` - Bottom side solder paste

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

## Parts

Description coming soon.

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
    gerber=True, svg=True, bom=True, centroids=True, povray=False)
```

The `in_subdir` argument specifies whether a subfolder named `basename` should be created for the assets.
The `gerber`, `svg`, `bom`, `centroids`, `povray` arguments specify which of the asset types to generate.


## To Do

- Expand default/basic parts library
- Routeing and Nets
- DRC checking
- More tests
- CI

## Releases

None yet.

## Authors

**pcbflow** was written by [Michael Gale](https://github.com/michaelgale) and is based on the [CuFlow](https://github.com/jamesbowman/cuflow) package by James Bowman.
