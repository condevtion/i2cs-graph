""" The submodule provides a set of functions to generate time sequences """

import datetime
import typing

import matplotlib.dates
import tzlocal
import pytz

_MINUTE = 60
_HOUR = 60
_DAY = 24
_WEEK = 7

def span_str(dt: float) -> str:
    """ Convert timespan expressed in days to a human readable string """
    s = []

    w = int(dt/_WEEK)
    r = dt%_WEEK
    if w > 0:
        s.append(f'{w}w')

    d = int(r)
    r -= d
    if d > 0 or s:
        s.append(f'{d}d')

    r *= _DAY
    h = int(r)
    r -= h
    if h > 0 or s:
        s.append(f'{h:02d}h')

    r *= _HOUR
    m = int(r)
    r -= m
    if m > 0 or s:
        s.append(f'{m:02d}m')

    s.append(f'{r*_MINUTE:06.3f}s')

    return ' '.join(s)

def _adjust_datetime(t: datetime.datetime, tz: typing.Any) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(t.timestamp()).astimezone(tz)

def _date2float(t: datetime.datetime) -> float:
    return float(matplotlib.dates.date2num(t))

_dt = datetime.timedelta(hours=1)
def _move_bkd_hour(t: datetime.datetime, h: typing.SupportsIndex,
                    tz: typing.Any) -> datetime.datetime:
    while t.hour != h:
        t = _adjust_datetime(t - _dt, tz)
    return t

def _move_fwd_hour(t: datetime.datetime, h: typing.SupportsIndex,
                    tz: typing.Any) -> datetime.datetime:
    while t.hour != h:
        t = _adjust_datetime(t + _dt, tz)
    return t

def _move_fwd_next_hour(t: datetime.datetime, h: typing.SupportsIndex,
                    tz: typing.Any) -> datetime.datetime:
    return _move_fwd_hour(_adjust_datetime(t + _dt, tz), h, tz)

def _move_bkd_weekday(t: datetime.datetime, w: int,
                    tz: typing.Any) -> datetime.datetime:
    while t.weekday() != w or t.hour != 0:
        t = _adjust_datetime(t - _dt, tz)
    return t

def _move_fwd_weekday(t: datetime.datetime, w: int,
                    tz: typing.Any) -> datetime.datetime:
    while t.weekday() != w or t.hour != 0:
        t = _adjust_datetime(t + _dt, tz)
    return t

def _move_fwd_next_weekday(t: datetime.datetime, w: int,
                    tz: typing.Any) -> datetime.datetime:
    while t.weekday() == w:
        t = _adjust_datetime(t + _dt, tz)
    return _move_fwd_weekday(t, w, tz)

type _SequenceGenerator = typing.Generator[tuple[float|None, float], None, None]

def make_time_sequence_15s(start: float, tzname: str|None = None) -> _SequenceGenerator:
    """ Generate a sequence of 15 seconds intervals centered at whole 15 seconds timestamps
        convering the given start point """
    if tzname is None:
        tzname = tzlocal.get_localzone().key
    tz = pytz.timezone(tzname)

    start_dt = matplotlib.dates.num2date(start, tz)
    second = int(start_dt.second/15)*15
    start_left = datetime.datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, start_dt.minute, second, 0,
            start_dt.tzinfo
        )

    dt_7_5sec = datetime.timedelta(seconds=7, milliseconds=500)
    if start_dt - start_left < dt_7_5sec:
        boundary_dt = _adjust_datetime(start_left - dt_7_5sec, tz)
    else:
        boundary_dt = _adjust_datetime(start_left + dt_7_5sec, tz)

    boundary = _date2float(boundary_dt)
    yield None, boundary
    prev = boundary

    dt_15sec = datetime.timedelta(seconds=15)
    while True:
        boundary_dt = _adjust_datetime(boundary_dt + dt_15sec, tz)

        boundary = _date2float(boundary_dt)
        yield (prev + boundary)/2, boundary
        prev = boundary

def make_time_sequence_1m(start: float, tzname: str|None = None) -> _SequenceGenerator:
    """ Generate a sequence of minute intervals centered at whole minute boundary convering
        the given start point """
    if tzname is None:
        tzname = tzlocal.get_localzone().key
    tz = pytz.timezone(tzname)

    start_dt = matplotlib.dates.num2date(start, tz)
    start_left = datetime.datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, start_dt.minute, 0, 0,
            start_dt.tzinfo
        )

    dt_30sec = datetime.timedelta(seconds=30)
    if start_dt - start_left < dt_30sec:
        boundary_dt = _adjust_datetime(start_left - dt_30sec, tz)
    else:
        boundary_dt = _adjust_datetime(start_left + dt_30sec, tz)

    boundary = _date2float(boundary_dt)
    yield None, boundary
    prev = boundary

    dt_1m = datetime.timedelta(minutes=1)
    while True:
        boundary_dt = _adjust_datetime(boundary_dt + dt_1m, tz)

        boundary = _date2float(boundary_dt)
        yield (prev + boundary)/2, boundary
        prev = boundary

def make_time_sequence_15m(start: float, tzname: str|None = None) -> _SequenceGenerator:
    """ Generate a sequence of 15 minute intervals centered at whole 15 minutes timestamps convering
        the given start point """
    if tzname is None:
        tzname = tzlocal.get_localzone().key
    tz = pytz.timezone(tzname)

    start_dt = matplotlib.dates.num2date(start, tz)
    minute = int(start_dt.minute/15)*15
    start_left = datetime.datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, minute, 0, 0,
            start_dt.tzinfo
        )

    dt_7m30s = datetime.timedelta(minutes=7, seconds=30)
    if start_dt - start_left < dt_7m30s:
        boundary_dt = _adjust_datetime(start_left - dt_7m30s, tz)
    else:
        boundary_dt = _adjust_datetime(start_left + dt_7m30s, tz)

    boundary = _date2float(boundary_dt)
    yield None, boundary
    prev = boundary

    dt_15m = datetime.timedelta(minutes=15)
    while True:
        boundary_dt = _adjust_datetime(boundary_dt + dt_15m, tz)

        boundary = _date2float(boundary_dt)
        yield (prev + boundary)/2, boundary
        prev = boundary

def make_time_sequence_1h(start: float, tzname: str|None = None) -> _SequenceGenerator:
    """ Generate a sequence of hour intervals centered at whole hour boundary convering the given
        start point """
    if tzname is None:
        tzname = tzlocal.get_localzone().key
    tz = pytz.timezone(tzname)

    start_dt = matplotlib.dates.num2date(start, tz)
    start_left = datetime.datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, 0, 0, 0,
            start_dt.tzinfo
        )

    dt_30m = datetime.timedelta(minutes=30)
    if start_dt - start_left < dt_30m:
        boundary_dt = _adjust_datetime(start_left - dt_30m, tz)
    else:
        boundary_dt = _adjust_datetime(start_left + dt_30m, tz)

    boundary = _date2float(boundary_dt)
    yield None, boundary
    prev = boundary

    dt_1h = datetime.timedelta(hours=1)
    while True:
        boundary_dt = _adjust_datetime(boundary_dt + dt_1h, tz)

        boundary = _date2float(boundary_dt)
        yield (prev + boundary)/2, boundary
        prev = boundary

def make_time_sequence_1d(start: float, tzname: str|None = None) -> _SequenceGenerator:
    """ Generate a sequence of day intervals centered at noon convering the given start point """
    if tzname is None:
        tzname = tzlocal.get_localzone().key
    tz = pytz.timezone(tzname)

    start_dt = matplotlib.dates.num2date(start, tz)
    boundary = _move_bkd_hour(datetime.datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, 0, 0, 0,
            start_dt.tzinfo
        ), 0, tz)

    yield None, _date2float(boundary)

    while True:
        center = _move_fwd_next_hour(boundary, 12, tz)
        boundary = _move_fwd_next_hour(boundary, 0, tz)

        yield _date2float(center), _date2float(boundary)

def make_time_sequence_1w(start: float, tzname: str|None = None) -> _SequenceGenerator:
    """ Generate a sequence of day intervals centered at noon convering the given start point """
    if tzname is None:
        tzname = tzlocal.get_localzone().key
    tz = pytz.timezone(tzname)

    start_dt = matplotlib.dates.num2date(start, tz)
    boundary_dt = _move_bkd_weekday(datetime.datetime(
            start_dt.year, start_dt.month, start_dt.day,
            start_dt.hour, 0, 0, 0,
            start_dt.tzinfo
        ), 0, tz)

    prev = _date2float(boundary_dt)
    yield None, prev

    while True:
        boundary_dt = _move_fwd_next_weekday(boundary_dt, 0, tz)

        boundary = _date2float(boundary_dt)
        yield prev, boundary
        prev = boundary

SCALES = (
    (15/_MINUTE/_HOUR/_DAY, make_time_sequence_15s, '15 seconds'),
    (1/_HOUR/_DAY, make_time_sequence_1m, 'minute'),
    (15/_HOUR/_DAY, make_time_sequence_15m, '15 minutes'),
    (1/_DAY, make_time_sequence_1h, 'hour'),
    (1, make_time_sequence_1d, 'day'),
    (_WEEK, make_time_sequence_1w, 'week'),
)

type Sequencer =  typing.Callable[[float], _SequenceGenerator]

def skip_seq_item(seq: _SequenceGenerator):
    """ Skip an item from the time sequence generator. Raise a runtime error if there is no item
        (as the generaor expected to be endless) """
    try:
        next(seq)
    except StopIteration as e:
        raise RuntimeError('Time sequence has ended unexpectedly') from e

def next_seq_item(seq: _SequenceGenerator) -> tuple[float, float]:
    """ Get next pair of a reference time and a period end from the time sequence generator. Raise
        a runtime error if there is no item (as the generaor expected to be endless) or if
        the reference time is None (it expected to be not None for each item except the first one)
    """
    try:
        ref, right = next(seq)
    except StopIteration as e:
        raise RuntimeError('Time sequence has ended unexpectedly') from e

    if ref is None:
        raise RuntimeError('Invalid time sequence item')

    return ref, right
