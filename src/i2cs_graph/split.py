""" The submodule provides plotting routine for a split chart """

import dataclasses

import tzlocal
import matplotlib.pyplot
import matplotlib.axes
import matplotlib.dates
import matplotlib.artist

from .read import Data, Timestamps
from .scale import DataSet, ResampledData, ScaleSelector, XLimits, BUCKETS
from .plot import AvgSeries, AvgLogSeries, ColorBackground
from .plot import T_COLOR, P_COLOR, RH_COLOR, AL_COLOR, IR_COLOR, R_COLOR, G_COLOR, B_COLOR

@dataclasses.dataclass(frozen=True)
class _Axes:
    t: matplotlib.axes.Axes
    p: matplotlib.axes.Axes
    rh: matplotlib.axes.Axes
    al: matplotlib.axes.Axes
    c: matplotlib.axes.Axes
    cs: matplotlib.axes.Axes

    def __init__(self):
        _, axs = matplotlib.pyplot.subplots(nrows=3, ncols=1, sharex=True, layout='constrained')
        t, al, cs = axs
        object.__setattr__(self, "t", t)
        object.__setattr__(self, "al", al)
        object.__setattr__(self, "cs", cs)

        locator = matplotlib.dates.AutoDateLocator()
        t.xaxis.set(
            major_locator=locator,
            major_formatter=matplotlib.dates.ConciseDateFormatter(
                locator,
                tz=tzlocal.get_localzone()
            )
        )
        t.set_ylabel('Temperature, °C')
        t.set_facecolor('none')

        al.set_ylabel('Illuminance, lux')
        al.set_facecolor('none')

        cs.set_ylabel('Normalized Color, %')

        p = t.twinx()
        object.__setattr__(self, "p", p)
        p.set_ylabel('Pressure, mbar')

        rh = t.twinx()
        object.__setattr__(self, "rh", rh)
        rh.spines['right'].set_position(('outward', 60))
        rh.set_facecolor('w')
        rh.set_ylabel('Humidity, %')

        t.set_zorder(3)
        p.set_zorder(2)
        rh.set_zorder(1)

        c = al.twinx()
        object.__setattr__(self, "c", c)
        c.set_facecolor('w')
        c.set_ylabel('Relative Response, %')

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
        self.__ir = AvgLogSeries((ts, data.al.ir), axes.c, 'IR, %', IR_COLOR)

    def update(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        self.__al.update(ts, data.al.al, limits)
        self.__ir.update(ts, data.al.ir, limits)

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__al.get_handle(), self.__ir.get_handle()

class _Color:
    def __init__(self, axes: _Axes, ts: Timestamps, data: ResampledData|Data):
        self.__r, = axes.cs.plot(ts, data.al.c.r, label='R, %', color=R_COLOR)
        self.__g, = axes.cs.plot(ts, data.al.c.g, label='G, %', color=G_COLOR)
        self.__b, = axes.cs.plot(ts, data.al.c.b, label='B, %', color=B_COLOR)

    def update(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        start, end = limits.start, limits.end
        self.__r.set_data(ts, data.al.c.r[start:end])
        self.__g.set_data(ts, data.al.c.g[start:end])
        self.__b.set_data(ts, data.al.c.b[start:end])

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__r, self.__g, self.__b

def plot_split(data_set: DataSet):
    """ Plot a split chart using the given dataset """

    axes = _Axes()

    data = data_set.overview if data_set.overview is not None else data_set.orig
    atm = _Atmospheric(axes, *data)
    al = _AmbientLight(axes, *data)
    clr = _Color(axes, *data)
    bkg = ColorBackground(axes.cs, BUCKETS)

    axes.t.legend(handles=atm.get_handles())
    axes.al.legend(handles=al.get_handles())
    axes.cs.legend(handles=clr.get_handles())

    atm_sel = ScaleSelector(data_set, atm.update)
    atm_sel.connect(axes.t)

    al_sel = ScaleSelector(data_set, al.update)
    al_sel.connect(axes.al)

    def clr_update(ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        bkg.update(ts, data, limits)
        clr.update(ts, data, limits)
    clr_sel = ScaleSelector(data_set, clr_update)
    clr_sel.connect(axes.cs)

    matplotlib.pyplot.show()
