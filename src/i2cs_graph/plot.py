""" The submodule provides plotting routine """

import dataclasses

import tzlocal
import matplotlib.pyplot
import matplotlib.axes
import matplotlib.dates
import matplotlib.artist

from .read import Data
from .scale import DataSet, Timestamps, ResampledData, ResampledValue
from .scale import ScaleSelector, XLimits

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

type _SeriesData = tuple[Timestamps, ResampledValue|tuple[float, ...]]
type _Data = tuple[Timestamps, ResampledData|Data]

class _AvgSeries:
    def __init__(self, data: _SeriesData, axes: matplotlib.axes.Axes, label: str, color: str):
        x, y = data

        if isinstance(y, ResampledValue):
            self.__line, = axes.plot(x, y.avg, label=label, color=color)
            self.__range = axes.fill_between(x, y.mn, y.mx, facecolor=color, alpha=0.3)
        else:
            self.__line, = axes.plot(x, y, label=label, color=color)
            self.__range = axes.fill_between((), (), (), facecolor=color, alpha=0.3)

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

class _Atmosperic:
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
        self.__al = _AvgSeries((ts, values.al.al), axes.al, 'I, lux', _AL_COLOR)
        self.__ir = _AvgSeries((ts, values.al.ir), axes.c, 'IR, %', _IR_COLOR)

    def update(self, data: _Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        ts, values = data
        self.__al.update((ts, values.al.al), limits)
        self.__ir.update((ts, values.al.ir), limits)

    def get_handles(self) -> tuple[matplotlib.artist.Artist, ...]:
        """ Return main handles for the atmospheric series """
        return self.__al.get_handle(), self.__ir.get_handle()

def plot(data_set: DataSet):
    """ Plot a chart using the given dataset """

    axes = _Axes()

    data = data_set.overview if data_set.overview is not None else data_set.orig
    atm = _Atmosperic(axes, data)
    al = _AmbientLight(axes, data)

    axes.t.legend(handles=atm.get_handles() + al.get_handles())

    def update(ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        atm.update((ts, data), limits)
        al.update((ts, data), limits)
    sel = ScaleSelector(data_set, update)
    sel.connect(axes.t)

    matplotlib.pyplot.show()
