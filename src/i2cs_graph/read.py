""" The submodule provides reader for CSV formatted i2cs-test script data """

import typing
import os.path
import csv
import dataclasses
import argparse

import dateutil
import numpy
import matplotlib.dates

from .error import Error

def parse_timestamp(s: str, **_) -> float:
    """ Parse the given string as a timestamp """
    if not s:
        raise Error('timestamp is empty')

    try:
        return float(matplotlib.dates.date2num(dateutil.parser.parse(s)))
    except dateutil.parser.ParserError as e:
        raise Error(f'can\'t parse timestamp: {e}') from e
    except OverflowError as e:
        raise Error(f'can\'t parse timestamp: one of numerical values in "{s}" overflows '
                     'parser') from e

def parse_value(s: str, desc: str, **_) -> float:
    """ Parse the given string as a floating point number """
    if not s:
        return numpy.nan

    try:
        return float(s)
    except ValueError as e:
        raise Error(f'can\'t parse "{s}" as {desc}') from e

def parse_pressure_value(s: str, **_) -> float:
    """ Parse the given string as a pressure sensor value """
    return parse_value(s, 'a pressure value')/100

ALS_DEFAULT_RESOLUTION = 18
ALS_SENSITIVITY = {
    16: 0.059,
    17: 0.029,
    18: 0.015,
    19: 0.007,
    20: 0.003,
}

def parse_illuminance_value(s: str, settings: argparse.Namespace) -> float:
    """ Parse the given string as a illuminance sensor value """
    v = parse_value(s, 'an illuminance value')
    return v if v > 0 else ALS_SENSITIVITY[settings.als_resolution]

def parse_color_value(s: str, desc: str, settings: argparse.Namespace) -> float:
    """ Parse the given string as a color sensor readings and return a normalized value based on
        the sensor's resolution """
    v = parse_value(s, f'{desc} sensor\'s value')
    if v <= 0:
        v = 0.5
    return v/(2**settings.als_resolution - 1)

type DataRow = tuple[float, ...]

_PARSERS = (
    (parse_timestamp, ()),
    (parse_pressure_value, ()),
    (parse_value, ('a temperature value from pressure sensor',)),
    (parse_value, ('a relative humidity value',)),
    (parse_value, ('a temperature value from relative humidity sensor',)),
    (parse_value, ('a gain value',)),
    (parse_illuminance_value, ()),
    (parse_color_value, ('an infrared',)),
    (parse_color_value, ('a red',)),
    (parse_color_value, ('a green',)),
    (parse_color_value, ('a blue',)),
)

def parse(row: list[str],
          settings: argparse.Namespace) -> typing.Generator[float, None, None]:
    """ Parse the given data row and yield a result per column """
    for i, (parser, args) in enumerate(_PARSERS):
        try:
            s = row[i].strip()
        except IndexError as e:
            raise Error(f'row "{", ".join(row)}" too short, '
                        f'expected {len(_PARSERS)} values, got {len(row)}') from e

        yield parser(s, *args, settings=settings)

_HEADER = ['time', 'p', 'tps', 'rh', 'trhs', 'gain', 'al', 'ir', 'r', 'g', 'b']

def parse_header(row: list[str],
                 settings: argparse.Namespace) -> tuple[typing.Callable, DataRow|None]:
    """ Check if the given row is the header and proceed to data parsing. If the row is not empty
        and not the header try to parse it as a data row """
    if list(map(lambda x: x.strip().lower(), row)) == _HEADER:
        return parse_data, None

    try:
        return parse_data(row, settings)
    except Error as e:
        raise Error(f'Unexpected header "{", ".join(row)}" ({e})') from e

def parse_data(row: list[str],
               settings: argparse.Namespace) -> tuple[typing.Callable, DataRow|None]:
    """ Parse the given row as a data row """
    return parse_data, tuple(parse(row, settings))

def read_csv(r: typing.Iterable[list[str]],
             settings: argparse.Namespace) -> typing.Generator[DataRow, None, None]:
    """ Read i2cs-test script data from the given CSV reader """
    parse_row = parse_header
    for n, row in enumerate(r, start=1):
        if not row:
            continue

        try:
            parse_row, data = parse_row(row, settings)
        except Error as e:
            raise Error(f'{n}: {e}') from e

        if data is not None:
            yield data

type Timestamps = tuple[float, ...]

@dataclasses.dataclass(frozen=True)
class Pressure:
    """ Holds pressure sensor data """
    p: tuple[float, ...]
    t: tuple[float, ...]

@dataclasses.dataclass(frozen=True)
class RelativeHumidity:
    """ Holds relative humidity sensor data """
    rh: tuple[float, ...]
    t: tuple[float, ...]

@dataclasses.dataclass(frozen=True)
class Color:
    """ Holds color part of ambient light sensor data """
    r: tuple[float, ...]
    g: tuple[float, ...]
    b: tuple[float, ...]

@dataclasses.dataclass(frozen=True)
class AmbientLight:
    """ Holds ambient light sensor data """
    gain: tuple[float, ...]
    al: tuple[float, ...]
    ir: tuple[float, ...]
    c: Color

@dataclasses.dataclass(frozen=True)
class Data:
    """ Holds sensor data table split by source """
    p: Pressure
    rh: RelativeHumidity
    al: AmbientLight

def read(path: str, settings: argparse.Namespace) -> tuple[Timestamps, Data]:
    """ Read CSV formatted i2cs-test script data from the given file """
    name = os.path.basename(path)
    with open(path, 'r', encoding='utf8', errors='replace') as f:
        try:
            columns = tuple(zip(*read_csv(csv.reader(f), settings)))
        except Error as e:
            raise Error(f'{name}:{e}') from e

    if not columns:
        raise Error(f'{name}: No data in the file')

    return columns[0], Data(
            Pressure(*columns[1:3]),
            RelativeHumidity(*columns[3:5]),
            AmbientLight(
                columns[5], columns[6], columns[7],
                Color(*columns[8:]),
            ),
        )
