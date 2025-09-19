""" This submodule provides tools to downsample data for efficient rendering when visualizing
    large datasets """

import dataclasses

import typing

import numpy

from .read import Timestamps, Data, Pressure, RelativeHumidity, AmbientLight
from .sequencer import span_str, SCALES, Sequencer, skip_seq_item, next_seq_item

@dataclasses.dataclass(frozen=True)
class ResampledValue:
    """ Holds resampled data """
    avg: tuple[float, ...]
    mn: tuple[float, ...]
    mx: tuple[float, ...]

@dataclasses.dataclass(frozen=True)
class ResampledPressure:
    """ Holds pressure resampled data """
    p: ResampledValue
    t: ResampledValue

@dataclasses.dataclass(frozen=True)
class ResampledRelativeHumidity:
    """ Holds relative humidity resampled data """
    rh: ResampledValue
    t: ResampledValue

@dataclasses.dataclass(frozen=True)
class ResampledAmbientLight:
    """ Holds ambient light resampled data """
    gain: ResampledValue
    al: ResampledValue
    ir: ResampledValue

@dataclasses.dataclass(frozen=True)
class ResampledData:
    """ Holds downsampled data table split by source """
    p: ResampledPressure
    rh: ResampledRelativeHumidity
    al: ResampledAmbientLight

@dataclasses.dataclass(frozen=True)
class DataSet:
    """ Holds original data and downsampled data for differend scales """
    orig: tuple[Timestamps, Data]
    scaled: dict[float, tuple[Timestamps, ResampledData]] = dataclasses.field(default_factory=dict)
    overview: tuple[Timestamps, ResampledData]|None = None

def _avg_not_nan(data: tuple[float, ...]) -> float:
    n = 0
    s = 0
    for x in data:
        if x is numpy.nan:
            continue
        s += x
        n += 1

    if n > 0:
        return s/n

    return numpy.nan

def _min_not_nan(data: tuple[float, ...]) -> float:
    m = numpy.nan
    for x in data:
        if x is numpy.nan:
            continue
        if m is numpy.nan or m > x:
            m = x

    return m

def _max_not_nan(data: tuple[float, ...]) -> float:
    m = numpy.nan
    for x in data:
        if x is numpy.nan:
            continue
        if m is numpy.nan or m < x:
            m = x

    return m

class _ValueBucket:
    def __init__(self):
        self.__n = 0
        self.__val = 0
        self.__min = numpy.nan
        self.__max = numpy.nan

    def add(self, val: float):
        """ Add the given value to the bucket """
        if val is numpy.nan:
            return

        self.__n += 1
        self.__val += val

        if self.__min is numpy.nan or self.__min > val:
            self.__min = val

        if self.__max is numpy.nan or self.__max < val:
            self.__max = val

    def summarize(self) -> tuple[float, float, float]:
        """ Summarize bucket's content """
        if self.is_empty():
            return numpy.nan, self.__min, self.__max

        return self.__val/self.__n, self.__min, self.__max

    def is_empty(self) -> bool:
        """ Check if the bucket is empty """
        return self.__n <= 0

type _ResampledPressureRow = tuple[float, float, float, float, float, float]

class _PressureBucket:
    def __init__(self):
        self.__p = _ValueBucket()
        self.__t = _ValueBucket()

    def add(self, p: float, t: float):
        """ Add the given values of pressure and temperature to the bucket """
        self.__p.add(p)
        self.__t.add(t)

    def summarize(self) -> _ResampledPressureRow:
        """ Summarize bucket's content """
        return self.__p.summarize() + self.__t.summarize()

type _ResampledAmbientLightRow = tuple[
        float, float, float, float, float, float, float, float, float
    ]

class _AmbientLightBucket:
    def __init__(self):
        self.__gain = _ValueBucket()
        self.__al = _ValueBucket()
        self.__ir = _ValueBucket()

    def add(self, gain: float, al: float, ir: float):
        """ Add the given values of pressure and temperature to the bucket """
        self.__gain.add(gain)
        self.__al.add(al)
        self.__ir.add(ir)

    def summarize(self) -> _ResampledAmbientLightRow:
        """ Summarize bucket's content """
        return self.__gain.summarize() + self.__al.summarize() + self.__ir.summarize()

type _ResampledRelativeHumidityRow = tuple[float, float, float, float, float, float]

class _RelativeHumidityBucket:
    def __init__(self):
        self.__rh = _ValueBucket()
        self.__t = _ValueBucket()

    def add(self, rh: float, t: float):
        """ Add the given values of pressure and temperature to the bucket """
        self.__rh.add(rh)
        self.__t.add(t)

    def summarize(self) -> _ResampledRelativeHumidityRow:
        """ Summarize bucket's content """
        return self.__rh.summarize() + self.__t.summarize()

type _ResampledDataRow = tuple[
    float, float, float, float, float, float,
    float, float, float, float, float, float,
    float, float, float, float, float, float, float, float, float
]

class _Bucket:
    def __init__(self):
        self.__p = _PressureBucket()
        self.__rh = _RelativeHumidityBucket()
        self.__al = _AmbientLightBucket()

    def add(self, data: Data, i: int):
        """ Add values of the given data sequence at the given index to the bucket """
        self.__p.add(data.p.p[i], data.p.t[i])
        self.__rh.add(data.rh.rh[i], data.rh.t[i])
        self.__al.add(data.al.gain[i], data.al.al[i], data.al.ir[i])

    def summarize(self) -> _ResampledDataRow:
        """ Summarize bucket's content """
        return self.__p.summarize() + self.__rh.summarize() + self.__al.summarize()

type _ResampledRow = tuple[
    float,
    float, float, float, float, float, float,
    float, float, float, float, float, float,
    float, float, float, float, float, float, float, float, float
]

def downsample(tsdata: tuple[Timestamps, Data],
               seq: Sequencer) -> typing.Generator[_ResampledRow, None, None]:
    """ Generate a downsampled data sequence from the given data into time intervals produced by
        the given time sequencer """
    ts, data = tsdata
    boundary = seq(ts[0])
    skip_seq_item(boundary)

    ts_seq = enumerate(ts)
    try:
        i, t = next(ts_seq)
    except StopIteration as e:
        raise RuntimeError('Time sequence has ended unexpectedly') from e

    while True:
        ref, right = next_seq_item(boundary)

        bucket = _Bucket()
        while t < right:
            bucket.add(data, i)
            try:
                i, t = next(ts_seq)
            except StopIteration:
                yield ref, *bucket.summarize()
                return

        yield ref, *bucket.summarize()

def _make_pressure_overview(p: Pressure, m: int) -> ResampledPressure:
    return ResampledPressure(
            ResampledValue(
                (_avg_not_nan(p.p[:m]), _avg_not_nan(p.p[m:])),
                (_min_not_nan(p.p[:m]), _min_not_nan(p.p[m:])),
                (_max_not_nan(p.p[:m]), _max_not_nan(p.p[m:]))
            ),
            ResampledValue(
                (_avg_not_nan(p.t[:m]), _avg_not_nan(p.t[m:])),
                (_min_not_nan(p.t[:m]), _min_not_nan(p.t[m:])),
                (_max_not_nan(p.t[:m]), _max_not_nan(p.t[m:]))
            ),
        )

def _make_relative_humidity_overview(rh: RelativeHumidity, m: int) -> ResampledRelativeHumidity:
    return ResampledRelativeHumidity(
            ResampledValue(
                (_avg_not_nan(rh.rh[:m]), _avg_not_nan(rh.rh[m:])),
                (_min_not_nan(rh.rh[:m]), _min_not_nan(rh.rh[m:])),
                (_max_not_nan(rh.rh[:m]), _max_not_nan(rh.rh[m:]))
            ),
            ResampledValue(
                (_avg_not_nan(rh.t[:m]), _avg_not_nan(rh.t[m:])),
                (_min_not_nan(rh.t[:m]), _min_not_nan(rh.t[m:])),
                (_max_not_nan(rh.t[:m]), _max_not_nan(rh.t[m:]))
            ),
        )

def _make_ambient_light_overview(al: AmbientLight, m: int) -> ResampledAmbientLight:
    return ResampledAmbientLight(
            ResampledValue(
                (_avg_not_nan(al.gain[:m]), _avg_not_nan(al.gain[m:])),
                (_min_not_nan(al.gain[:m]), _min_not_nan(al.gain[m:])),
                (_max_not_nan(al.gain[:m]), _max_not_nan(al.gain[m:]))
            ),
            ResampledValue(
                (_avg_not_nan(al.al[:m]), _avg_not_nan(al.al[m:])),
                (_min_not_nan(al.al[:m]), _min_not_nan(al.al[m:])),
                (_max_not_nan(al.al[:m]), _max_not_nan(al.al[m:]))
            ),
            ResampledValue(
                (_avg_not_nan(al.ir[:m]), _avg_not_nan(al.ir[m:])),
                (_min_not_nan(al.ir[:m]), _min_not_nan(al.ir[m:])),
                (_max_not_nan(al.ir[:m]), _max_not_nan(al.ir[m:]))
            ),
        )

def make_overview(tsdata: tuple[Timestamps, Data]) -> tuple[Timestamps, ResampledData]:
    """ Produce a two point "overview" for the given data. The overview attributes averages,
        minimums, and maximums of the first half of data to the earliest timestamp, and the same of
        the second half to the latest one """

    ts, data = tsdata
    m = int(len(ts)/2)
    return (
        (ts[0], ts[-1]),
        ResampledData(
            _make_pressure_overview(data.p, m),
            _make_relative_humidity_overview(data.rh, m),
            _make_ambient_light_overview(data.al, m),
        ),
    )

def prescale(data: tuple[Timestamps, Data]) -> DataSet:
    """ Produce a dataset based on the given data which includes original data, suitable downscaled
        variants, and a two point "overview" """
    ts, _ = data
    if len(ts) < 100:
        return DataSet(data)

    span = ts[-1] - ts[0]
    print(f'\tspan............: {span_str(span)}')

    t_avg = span/(len(ts) - 1)
    print(f'\taverage interval: {span_str(t_avg)}')

    scaled = {}
    for scale, seq, desc in SCALES:
        bucket = scale/t_avg
        buckets = span/scale
        buckets = int(buckets) + 1 if buckets > int(buckets) else int(buckets)
        if bucket < 5 or buckets < 100 or seq is None:
            continue

        columns = tuple(zip(*downsample(data, seq)))
        scaled[scale] = (
                columns[0],
                ResampledData(
                    ResampledPressure(
                        ResampledValue(*columns[1:4]),
                        ResampledValue(*columns[4:7]),
                    ),
                    ResampledRelativeHumidity(
                        ResampledValue(*columns[7:10]),
                        ResampledValue(*columns[10:13]),
                    ),
                    ResampledAmbientLight(
                        ResampledValue(*columns[13:16]),
                        ResampledValue(*columns[16:19]),
                        ResampledValue(*columns[19:]),
                    ),
                )
            )

        print(f'\tscale: {span_str(scale)} ({desc}):')
        print(f'\t\tbuckets total....: {len(columns[0])}')
        print(f'\t\tpoints per bucket: {len(data[0])/len(columns[0]):.1f}')

    return DataSet(data, scaled, make_overview(data))
