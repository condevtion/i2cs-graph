""" Helper functions and definitions for tests """

import pytz
import matplotlib.dates

HOUR = 1/24
MINUTE = HOUR/60
SECOND = MINUTE/60

UTC = 'UTC'
PT = 'America/Los_Angeles'
TZ_NAMES = (
    UTC,
    PT,
)
TZ = {name: pytz.timezone(name) for name in TZ_NAMES}

def num2datestr(t, tzname, fmt):
    """ Convert the given number of days since epoh (1970-01-01 UTC) to a string representation of
        a timestamp in the given timezone """
    return matplotlib.dates.num2date(t, TZ[tzname]).strftime(fmt)

def gen_seq(n, *args):
    """ Generate a set of sequences of the given length defined by pairs of initial value and step
    """
    for i in range(n):
        yield tuple(x + i*dx for x, dx in args)

def distribute(seq, ts, tzname, fmt='%Y-%m-%d %H:%M:%S.%f %z'):
    """ Distribute the given timestamp series into groups limited with boundaries produced by
        the given sequencer """
    s = seq(ts[0], tzname)

    try:
        (_, left), (ref, right) = next(s), next(s)
    except StopIteration as e:
        raise RuntimeError('Time sequence has ended unexpectedly') from e

    bucket = (
            num2datestr(left, tzname, fmt), num2datestr(right, tzname, fmt),
            num2datestr(ref, tzname, fmt),
            [],
        )
    for t in ts:
        if t >= right:
            yield bucket

            try:
                left, (ref, right) = right, next(s)
            except StopIteration as e:
                raise RuntimeError('Time sequence has ended unexpectedly') from e

            bucket = (
                    num2datestr(left, tzname, fmt), num2datestr(right, tzname, fmt),
                    num2datestr(ref, tzname, fmt),
                    [],
                )

        bucket[-1].append(num2datestr(t, tzname, fmt))

    yield bucket
