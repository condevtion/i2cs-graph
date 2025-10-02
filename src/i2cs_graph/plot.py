""" The submodule provides plotting tools for time series data """

import typing

import matplotlib.axes
import matplotlib.artist
import matplotlib.patches
import numpy

from .read import Timestamps, Data
from .scale import ResampledValue, ResampledData, ColorBucket, XLimits
from .color import repr_color

type TimedValue = tuple[Timestamps, ResampledValue|tuple[float, ...]]

class AvgSeries:
    """ Holds a series with average and optional range """
    def __init__(self, data: TimedValue, axes: matplotlib.axes.Axes, label: str, color: str):
        x, y = data

        if isinstance(y, ResampledValue):
            self.__line, = self._plotter(axes)(x, y.avg, label=label, color=color)
            self.__range = axes.fill_between(x, y.mn, y.mx, facecolor=color, alpha=0.3)
        else:
            self.__line, = self._plotter(axes)(x, y, label=label, color=color)
            self.__range = axes.fill_between((), (), (), facecolor=color, alpha=0.3)

    @staticmethod
    def _plotter(axes: matplotlib.axes.Axes):
        return axes.plot

    def update(self, ts: Timestamps, data: ResampledValue|tuple[float, ...], limits: XLimits):
        """ Set the given data to line and fill if possible """
        start, end = limits.start, limits.end

        if isinstance(data, ResampledValue):
            self.__line.set_data(ts, data.avg[start:end])
            self.__range.set_data(ts, data.mn[start:end], data.mx[start:end])
        else:
            self.__line.set_data(ts, data[start:end])
            self.__range.set_data((), (), ())

    def get_handle(self) -> matplotlib.artist.Artist:
        """ Return main handle for the series """
        return self.__line

class AvgLogSeries(AvgSeries):
    """ Holds a series with average and optional range in logarithmic scale """
    @staticmethod
    def _plotter(axes: matplotlib.axes.Axes):
        return axes.semilogy

T_COLOR = 'tab:orange'
P_COLOR = 'tab:purple'
RH_COLOR = 'tab:olive'
AL_COLOR = 'tab:cyan'
IR_COLOR = 'tab:gray'
R_COLOR = 'tab:red'
G_COLOR = 'tab:green'
B_COLOR = 'tab:blue'

type _RectGen = typing.Generator[matplotlib.patches.Rectangle, None, None]

def _make_color_background(ax: matplotlib.axes.Axes, n: int) -> _RectGen:
    left, right = ax.get_xlim()
    dt = (right - left)/n

    for i in range(n):
        x = left + i*dt
        yield ax.axvspan(x, x + dt, visible=False, color='w')

    ax.set_xlim(left, right)

class _ColorSplicer: # pylint: disable=too-few-public-methods
    def __init__(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        start, end = limits.start, limits.end
        r = data.al.c.r[start:end]
        g = data.al.c.g[start:end]
        b = data.al.c.b[start:end]

        self.__colors = ((t, (r[i], g[i], b[i])) for i, t in enumerate(ts))
        self.t_prev = None
        self.c_prev = (numpy.nan, numpy.nan, numpy.nan)

        try:
            self.t, self.c = next(self.__colors)
        except StopIteration:
            self.t, self.c = None, (numpy.nan, numpy.nan, numpy.nan)

    def __fill(self, limit: float) -> ColorBucket:
        bucket = ColorBucket()
        while self.t is not None and self.t < limit:
            bucket.add(self.c)
            if self.t is not None:
                try:
                    self.t, self.c = next(self.__colors)
                except StopIteration:
                    self.t, self.c = None, (numpy.nan, numpy.nan, numpy.nan)

        return bucket

    def __best_neighbor(self, left: float, right: float) -> tuple[float, float, float]|None:
        if self.t_prev is not None and self.t is not None:
            mid = 0.5*(left + right)
            if abs(mid - self.t_prev) < abs(self.t - mid):
                return self.c_prev
            return self.c

        if self.t_prev is not None:
            return self.c_prev

        if self.t is not None:
            return self.c

        return None

    def get(self, left: float, right: float) -> tuple[float, float, float]|None:
        """ Returns a dominant or best neighbor color for the given boundaries """
        bucket = self.__fill(right)
        if bucket.is_empty():
            return self.__best_neighbor(left, right)

        return bucket.summarize()

type _Rectangles = tuple[matplotlib.patches.Rectangle, ...]
type _BoundRectangle = tuple[float, float, matplotlib.patches.Rectangle]
type _BoundRectangleGenerator = typing.Generator[_BoundRectangle, None, None]

def _enumerate_rectangles(rectangles: _Rectangles, limits: XLimits) -> _BoundRectangleGenerator:
    left, right = limits.left, limits.right
    dt = (right - left)/len(rectangles)

    for i, r in enumerate(rectangles):
        yield left + i*dt, dt, r

class ColorBackground: # pylint: disable=too-few-public-methods
    """ Renders color background according to color sensors readings """
    def __init__(self, axes: matplotlib.axes.Axes, n: int):
        self.__bkg = tuple(_make_color_background(axes, n))

    def update(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        """ Update color background according to given data slice """
        try:
            ts_min, ts_max = ts[0], ts[-1]
        except IndexError:
            for rec in self.__bkg:
                rec.set(visible=False)

            return

        colors = _ColorSplicer(ts, data, limits)
        for left, dt, r in _enumerate_rectangles(self.__bkg, limits):
            right = left + dt
            if left >= ts_max or right < ts_min:
                r.set(x=left, width=dt, visible=False)
                continue

            color = colors.get(left, right)
            if color is None:
                r.set(x=left, width=dt, visible=False)
                continue

            r.set(x=left, width=dt, visible=True, color=repr_color(*color))
