""" The submodule provides plotting routine """

import dataclasses
import typing

import tzlocal
import matplotlib.pyplot
import matplotlib.axes
import matplotlib.dates
import matplotlib.artist
import matplotlib.patches
import numpy

from .read import Data
from .scale import DataSet, Timestamps, ResampledData, ResampledValue, ColorBucket
from .scale import ScaleSelector, XLimits, BUCKETS
from .color import repr_color

@dataclasses.dataclass(frozen=True)
class _Axes:
    t: matplotlib.axes.Axes
    p: matplotlib.axes.Axes
    rh: matplotlib.axes.Axes
    al: matplotlib.axes.Axes
    c: matplotlib.axes.Axes

    def __init__(self):
        _, t = matplotlib.pyplot.subplots(layout='constrained')
        object.__setattr__(self, "t", t)
        locator = matplotlib.dates.AutoDateLocator()
        t.xaxis.set(
            major_locator=locator,
            major_formatter=matplotlib.dates.ConciseDateFormatter(
                locator,
                tz=tzlocal.get_localzone()
            )
        )
        t.set_facecolor('none')
        t.set_xlabel('Time')
        t.set_ylabel('Temperature, °C')

        p = t.twinx()
        object.__setattr__(self, "p", p)
        p.spines['left'].set_position(('outward', 60))
        p.set_ylabel('Pressure, mbar')
        p.yaxis.set_label_position('left')
        p.yaxis.set_ticks_position('left')

        rh = t.twinx()
        object.__setattr__(self, "rh", rh)
        rh.spines['left'].set_position(('outward', 120))
        rh.set_ylabel('Humidity, %')
        rh.yaxis.set_label_position('left')
        rh.yaxis.set_ticks_position('left')

        al = t.twinx()
        object.__setattr__(self, "al", al)
        al.set_ylabel('Illuminance, lux')

        c = t.twinx()
        object.__setattr__(self, "c", c)
        c.set_facecolor('w')
        c.spines['right'].set_position(('outward', 60))
        c.set_ylabel('Color, %')

        t.set_zorder(5)
        p.set_zorder(4)
        rh.set_zorder(3)
        al.set_zorder(2)
        c.set_zorder(1)

_T_COLOR = 'tab:orange'
_P_COLOR = 'tab:purple'
_RH_COLOR = 'tab:olive'
_AL_COLOR = 'tab:cyan'
_IR_COLOR = 'tab:gray'
_R_COLOR = 'tab:red'
_G_COLOR = 'tab:green'
_B_COLOR = 'tab:blue'

type _SeriesData = tuple[Timestamps, ResampledValue|tuple[float, ...]]
type _Data = tuple[Timestamps, ResampledData|Data]

class _AvgSeries:
    def __init__(self, data: _SeriesData, axes: matplotlib.axes.Axes, label: str, color: str):
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

    def update(self, data: _SeriesData, limits: XLimits):
        """ Set the given data to line and fill if possible """
        x, y = data
        start, end = limits.start, limits.end

        if isinstance(y, ResampledValue):
            self.__line.set_data(x, y.avg[start:end])
            self.__range.set_data(x, y.mn[start:end], y.mx[start:end])
        else:
            self.__line.set_data(x, y[start:end])
            self.__range.set_data((), (), ())

    def get_handle(self) -> matplotlib.artist.Artist:
        """ Return main handle for the series """
        return self.__line

class _AvgLogSeries(_AvgSeries):
    @staticmethod
    def _plotter(axes: matplotlib.axes.Axes):
        return axes.semilogy

class _Atmospheric:
    def __init__(self, axes: _Axes, data: _Data):
        ts, values = data
        self.__t = _AvgSeries((ts, values.rh.t), axes.t, 'T, °C', _T_COLOR)
        self.__p = _AvgSeries((ts, values.p.p), axes.p, 'P, mbar', _P_COLOR)
        self.__rh = _AvgSeries((ts, values.rh.rh), axes.rh, 'RH, %', _RH_COLOR)

    def update(self, data: _Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        ts, values = data
        self.__t.update((ts, values.rh.t), limits)
        self.__p.update((ts, values.p.p), limits)
        self.__rh.update((ts, values.rh.rh), limits)

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__t.get_handle(), self.__p.get_handle(), self.__rh.get_handle()

class _AmbientLight:
    def __init__(self, axes: _Axes, data: _Data):
        ts, values = data
        self.__al = _AvgLogSeries((ts, values.al.al), axes.al, 'I, lux', _AL_COLOR)
        self.__ir = _AvgSeries((ts, values.al.ir), axes.c, 'IR, %', _IR_COLOR)
        self.__r, = axes.c.plot(ts, values.al.c.r, label='R, %', color=_R_COLOR)
        self.__g, = axes.c.plot(ts, values.al.c.g, label='G, %', color=_G_COLOR)
        self.__b, = axes.c.plot(ts, values.al.c.b, label='B, %', color=_B_COLOR)

    def update(self, data: _Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        ts, values = data
        self.__al.update((ts, values.al.al), limits)
        self.__ir.update((ts, values.al.ir), limits)

        start, end = limits.start, limits.end
        self.__r.set_data(ts, values.al.c.r[start:end])
        self.__g.set_data(ts, values.al.c.g[start:end])
        self.__b.set_data(ts, values.al.c.b[start:end])

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__al.get_handle(), self.__ir.get_handle(), self.__r, self.__g, self.__b

type _RectGen = typing.Generator[matplotlib.patches.Rectangle, None, None]

def _make_color_background(ax: matplotlib.axes.Axes, n: int) -> _RectGen:
    left, right = ax.get_xlim()
    dt = (right - left)/n

    for i in range(n):
        x = left + i*dt
        yield ax.axvspan(x, x + dt, visible=False, color='w')

    ax.set_xlim(left, right)

class _ColorSplicer: # pylint: disable=too-few-public-methods
    def __init__(self, data: _Data, limits: XLimits):
        ts, values = data
        start, end = limits.start, limits.end
        r = values.al.c.r[start:end]
        g = values.al.c.g[start:end]
        b = values.al.c.b[start:end]

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

class _ColorBackground: # pylint: disable=too-few-public-methods
    def __init__(self, axes: _Axes, n: int):
        self.__bkg = tuple(_make_color_background(axes.c, n))

    def update(self, data: _Data, limits: XLimits):
        """ Update color background according to given data slice """
        ts, _ = data
        try:
            ts_min, ts_max = ts[0], ts[-1]
        except IndexError:
            for rec in self.__bkg:
                rec.set(visible=False)

            return

        colors = _ColorSplicer(data, limits)
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

def plot(data_set: DataSet):
    """ Plot a chart using the given dataset """

    axes = _Axes()

    data = data_set.overview if data_set.overview is not None else data_set.orig
    atm = _Atmospheric(axes, data)
    al = _AmbientLight(axes, data)
    bkg = _ColorBackground(axes, BUCKETS)

    axes.t.legend(handles=atm.get_handles() + al.get_handles())

    def update(ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        atm.update((ts, data), limits)
        al.update((ts, data), limits)
        bkg.update((ts, data), limits)
    sel = ScaleSelector(data_set, update)
    sel.connect(axes.t)

    matplotlib.pyplot.show()
