# pcbflow - Python PCB layout and design (based on CuFlow)

![python version](https://img.shields.io/static/v1?label=python&message=3.6%2B&color=blue&style=flat&logo=python)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>  

This repository contains a python based Printed Circuit Board (PCB) layout and design package based on [CuFlow](https://github.com/jamesbowman/cuflow) by James Bowman.

This implementation is an experimental variation of CuFlow.  It attempts to modularize the components of CuFlow and extend/modify its functionality in some key areas:

- allow component placement on top or bottom (automatically chooses top or bottom companion layers of silkscreen, soldermask, copper)
- allow customization of track widths, drill/hole types
- contain design rules in a dictionary rather than the Board class
- improve layout metrics
- enhanced Gerber files with FileFunction assignements
- plus more

This implementation is very alpha and not documented.
