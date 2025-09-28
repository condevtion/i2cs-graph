""" The submodule gathers color processing calculations """
import enum
import colorsys

import numpy

# The RGB correction matrix based on measured response to LCD monitor:
# Light | Sensor R    | Sensor G    | Sensor B
# -----------------------------------------------
#  R      3484.479452   1374.013699    171.054795
#  G       836.113636   6412.068182   1322.522727
#  B       208.615385    864.169231   3491.615385
#  W      4495.967391   8601.402174   4942.413043
# Requires R, G rebalancing based on hue value ~10° (~600nm): R = 0.87×Rs, G = Gs + 0.13×Rs
# _LCD_RGB_MATRIX = (
#     (2.599738, -0.323473, -0.075269),
#     (-0.568966, 1.484395, -0.333391),
#     (0.088146, -0.546399, 2.593411),
# )
#
# Red sensor Hue correction from ~10° to ~0° (from ~600 to ~640nm)
# _LCD_HUE_MATRIX = (
#     (0.87, 0, 0),
#     (0.13, 1, 0),
#     (0, 0, 1),
# )
#
# _RGB_MATRIX = numpy.dot(_LCD_RGB_MATRIX, _LCD_HUE_MATRIX)

# The RGB correction matrix based on relative response approximation (see "APDS-9999 Digital
# Proximity and RGB Sensor", figure 1 - "Spectral Response"):
# Light | Sensor R | Sensor G | Sensor B
# --------------------------------------
#  R      0.875      0.3        0.015
#  G      0.06       0.975      0.1
#  B      0.05       0.13       0.625
_RGB_MATRIX = (
    (1.168, -0.08, 0.006),
    (-0.36, 1.071, -0.22),
    (0.03, -0.17, 1.635),
)

_AL_TRESHOLD = 7.395

def norm_color(al: float, r: float, g: float, b: float) -> tuple[float, float, float]:
    """ Normalizes RGB values to 0-100 range """
    if al == numpy.nan:
        w = 0
    else:
        w = al/_AL_TRESHOLD*100.0
        if w > 100.0:
            w = 100.0

    rs, gs, bs = numpy.dot(_RGB_MATRIX, (r, g, b))
    m = min(rs, gs, bs)
    if m < 4.7e-07:
        m -= 4.8e-07
        rs -= m
        gs -= m
        bs -= m

    m = max(rs, gs, bs)
    return float(rs/m*w), float(gs/m*w), float(bs/m*w)

def repr_color(r: float, g: float, b: float) -> str:
    """ Represents RGB color as a hex string """
    return f'#{int(r*2.55):02x}{int(g*2.55):02x}{int(b*2.55):02x}'

class Colors(enum.Enum):
    """ The enum defines a set of colors for RGB values grouping """
    KEY = object()
    WHITE = object()
    RED = object()
    YELLOW = object()
    GREEN = object()
    CYAN = object()
    BLUE = object()
    MAGENTA = object()

def classify_color(r: float, g: float, b: float) -> Colors:
    """ Assigns one of the Colors value to the given RGB value """
    h, l, _ = colorsys.rgb_to_hls(r/100., g/100., b/100.)
    if l >= 0.95:
        c = Colors.WHITE
    elif l < 0.05:
        c = Colors.KEY
    elif 1./12 < h <= 1./4:
        c = Colors.YELLOW
    elif 1./4 < h <= 5./12:
        c = Colors.GREEN
    elif 5./12 < h <= 7./12:
        c = Colors.CYAN
    elif 7./12 < h <= 3./4:
        c = Colors.BLUE
    elif 3./4 < h <= 11./12:
        c = Colors.MAGENTA
    else:
        c = Colors.RED

    return c
