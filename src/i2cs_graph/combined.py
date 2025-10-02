""" The submodule provides plotting routine for a combined chart """

import dataclasses

import tzlocal
import matplotlib.pyplot
import matplotlib.axes
import matplotlib.dates
import matplotlib.artist

from .read import Data, Timestamps
from .scale import DataSet, ResampledData
from .scale import ScaleSelector, XLimits, BUCKETS
from .plot import AvgSeries, AvgLogSeries, ColorBackground
from .plot import T_COLOR, P_COLOR, RH_COLOR, AL_COLOR, IR_COLOR, R_COLOR, G_COLOR, B_COLOR

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

class _Atmospheric:
    def __init__(self, axes: _Axes, ts: Timestamps, data: ResampledData|Data):
        self.__t = AvgSeries((ts, data.rh.t), axes.t, 'T, °C', T_COLOR)
        self.__p = AvgSeries((ts, data.p.p), axes.p, 'P, mbar', P_COLOR)
        self.__rh = AvgSeries((ts, data.rh.rh), axes.rh, 'RH, %', RH_COLOR)

    def update(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        self.__t.update(ts, data.rh.t, limits)
        self.__p.update(ts, data.p.p, limits)
        self.__rh.update(ts, data.rh.rh, limits)

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__t.get_handle(), self.__p.get_handle(), self.__rh.get_handle()

class _AmbientLight:
    def __init__(self, axes: _Axes, ts: Timestamps, data: ResampledData|Data):
        self.__al = AvgLogSeries((ts, data.al.al), axes.al, 'I, lux', AL_COLOR)
        self.__ir = AvgSeries((ts, data.al.ir), axes.c, 'IR, %', IR_COLOR)
        self.__r, = axes.c.plot(ts, data.al.c.r, label='R, %', color=R_COLOR)
        self.__g, = axes.c.plot(ts, data.al.c.g, label='G, %', color=G_COLOR)
        self.__b, = axes.c.plot(ts, data.al.c.b, label='B, %', color=B_COLOR)

    def update(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        self.__al.update(ts, data.al.al, limits)
        self.__ir.update(ts, data.al.ir, limits)

        start, end = limits.start, limits.end
        self.__r.set_data(ts, data.al.c.r[start:end])
        self.__g.set_data(ts, data.al.c.g[start:end])
        self.__b.set_data(ts, data.al.c.b[start:end])

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__al.get_handle(), self.__ir.get_handle(), self.__r, self.__g, self.__b

def plot_combined(data_set: DataSet):
    """ Plot a combined chart using the given dataset """

    axes = _Axes()

    data = data_set.overview if data_set.overview is not None else data_set.orig
    atm = _Atmospheric(axes, *data)
    al = _AmbientLight(axes, *data)
    bkg = ColorBackground(axes.c, BUCKETS)

    axes.t.legend(handles=atm.get_handles() + al.get_handles())

    def update(ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        atm.update(ts, data, limits)
        al.update(ts, data, limits)
        bkg.update(ts, data, limits)
    sel = ScaleSelector(data_set, update)
    sel.connect(axes.t)

    matplotlib.pyplot.show()
