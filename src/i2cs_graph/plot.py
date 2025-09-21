""" The submodule provides plotting routine """

import dataclasses

import tzlocal
import matplotlib.pyplot
import matplotlib.axes
import matplotlib.dates
import matplotlib.lines
import matplotlib.collections

from .read import Data
from .scale import DataSet, Timestamps, ResampledData
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

        t.set_zorder(5)
        p.set_zorder(4)
        rh.set_zorder(3)

_T_COLOR = 'tab:orange'
_P_COLOR = 'tab:purple'
_RH_COLOR = 'tab:olive'

@dataclasses.dataclass(frozen=True)
class _Atmosperic:
    t_line: matplotlib.lines.Line2D
    t_range: matplotlib.collections.FillBetweenPolyCollection

    p_line: matplotlib.lines.Line2D
    p_range: matplotlib.collections.FillBetweenPolyCollection

    rh_line: matplotlib.lines.Line2D
    rh_range: matplotlib.collections.FillBetweenPolyCollection

    def __init__(self, axes: _Axes, ts: Timestamps, data: ResampledData|Data):
        if isinstance(data, ResampledData):
            t, p, rh = data.rh.t.avg, data.p.p.avg, data.rh.rh.avg
        else:
            t, p, rh = data.rh.t, data.p.p, data.rh.rh

        t_line, = axes.t.plot(ts, t, label='T, °C', color=_T_COLOR)
        object.__setattr__(self, "t_line", t_line)

        p_line, = axes.p.plot(ts, p, label='P, mbar', color=_P_COLOR)
        object.__setattr__(self, "p_line", p_line)

        rh_line, = axes.rh.plot(ts, rh, label='RH, %', color=_RH_COLOR)
        object.__setattr__(self, "rh_line", rh_line)

        if isinstance(data, ResampledData):
            t_range = axes.t.fill_between(ts, data.rh.t.mn, data.rh.t.mx,
                                          facecolors=_T_COLOR, alpha=0.3)
            p_range = axes.p.fill_between(ts, data.p.p.mn, data.p.p.mx,
                                          facecolors=_P_COLOR, alpha=0.3)
            rh_range = axes.rh.fill_between(ts, data.rh.rh.mn, data.rh.rh.mx,
                                          facecolors=_RH_COLOR, alpha=0.3)
        else:
            t_range = axes.t.fill_between((), (), (), facecolors=_T_COLOR, alpha=0.3)
            p_range = axes.p.fill_between((), (), (), facecolors=_P_COLOR, alpha=0.3)
            rh_range = axes.rh.fill_between((), (), (), facecolors=_RH_COLOR, alpha=0.3)
        object.__setattr__(self, "t_range", t_range)
        object.__setattr__(self, "p_range", p_range)
        object.__setattr__(self, "rh_range", rh_range)

    def update(self, ts: Timestamps, data: ResampledData|Data, limits: XLimits):
        """ Set given data to the respective lines and fills """
        start, end = limits.start, limits.end

        if isinstance(data, ResampledData):
            self.t_line.set_data(ts, data.rh.t.avg[start:end])
            self.t_range.set_data(ts, data.rh.t.mn[start:end], data.rh.t.mx[start:end])

            self.p_line.set_data(ts, data.p.p.avg[start:end])
            self.p_range.set_data(ts, data.p.p.mn[start:end], data.p.p.mx[start:end])

            self.rh_line.set_data(ts, data.rh.rh.avg[start:end])
            self.rh_range.set_data(ts, data.rh.rh.mn[start:end], data.rh.rh.mx[start:end])
        else:
            self.t_line.set_data(ts, data.rh.t[start:end])
            self.t_range.set_data((), (), ())

            self.p_line.set_data(ts, data.p.p[start:end])
            self.p_range.set_data((), (), ())

            self.rh_line.set_data(ts, data.rh.rh[start:end])
            self.rh_range.set_data((), (), ())

def plot(data_set: DataSet):
    """ Plots a chart using the given dataset """

    axes = _Axes()

    data = data_set.overview if data_set.overview is not None else data_set.orig
    atm = _Atmosperic(axes, *data)

    axes.t.legend(handles=(atm.t_line, atm.p_line, atm.rh_line))

    sel = ScaleSelector(data_set, atm.update)
    sel.connect(axes.t)

    matplotlib.pyplot.show()
