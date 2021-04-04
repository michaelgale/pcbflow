#! /usr/bin/env python3
#
# Excellon drill file exporter
#

preamble = """\
M48
FMAT,2
ICI,OFF
METRIC,TZ,000.000
{0}%
G90
M71
{1}M30
"""


def excellon(f, holes, function):
    tools = sorted(holes.keys())
    p0 = "".join(["T%dC%.3f\n" % (i + 2, d) for (i, d) in enumerate(tools)])

    def number(n):
        i = int(round(n * 1000))
        return "%03d" % i

    def hits(i, xys):
        return ("T%d\n" % (i + 2)) + "".join(
            ["X%sY%s\n" % (number(xy[0]), number(xy[1])) for xy in xys]
        )

    # f.write("%%TF.FileFunction,%s*%%\n" % function)
    p1 = "".join([hits(i, holes[t]) for (i, t) in enumerate(tools)])
    f.write(preamble.format(p0, p1))
