""" Contains test for the read submodule """
import unittest
import argparse
import math

import numpy

import i2cs_graph.error
import i2cs_graph.read

_SETTINGS = argparse.Namespace(als_resolution=i2cs_graph.read.ALS_DEFAULT_RESOLUTION)
_MIN_COLOR_18 = 0.5/(2**18-1)
_SECOND = 1/24/60/60
_DATA_SAMPLE = (
    (20344, 20344 + _SECOND, 20344 + 2*_SECOND),
    i2cs_graph.read.Data(
        i2cs_graph.read.Pressure(
            (1000.0, 1000.0, 1000.0),
            (0.0, 0.0, 0.0)
        ),
        i2cs_graph.read.RelativeHumidity(
            (50.0, 50.0, 50.0),
            (0.0, 0.0, 0.0)
        ),
        i2cs_graph.read.AmbientLight(
            (18.0, 18.0, 18.0),
            (0.015, 0.015, 0.015),
            (2*_MIN_COLOR_18, 2*_MIN_COLOR_18, 2*_MIN_COLOR_18),
            i2cs_graph.read.Color(
                (_MIN_COLOR_18, _MIN_COLOR_18, _MIN_COLOR_18),
                (_MIN_COLOR_18, _MIN_COLOR_18, _MIN_COLOR_18),
                (_MIN_COLOR_18, _MIN_COLOR_18, _MIN_COLOR_18)
            )
        )
    )
)
_SAMPLE_RAW_ROW = [
    '2025-09-13 00:00:00.000000 +0000',
    '100000', '0',
    '50', '0',
    '18', '0', '1', '0', '0', '0',
]
_SAMPLE_DATA_ROW = (
    20344.0,
    1000.0, 0.0,
    50.0, 0.0,
    18.0, 0.015, 2*_MIN_COLOR_18, _MIN_COLOR_18, _MIN_COLOR_18, _MIN_COLOR_18,
)

class TestRead(unittest.TestCase):
    """ Tests for data reading functions """
    def test_read(self):
        """ A well formed data file can be read """
        data = i2cs_graph.read.read('./test/data/test.csv', _SETTINGS)
        self.assertEqual(data, _DATA_SAMPLE)

    def test_read_with_empty_lines(self):
        """ A well formed data file with empty lines as well can be read """
        data = i2cs_graph.read.read('./test/data/empty-lines.csv', _SETTINGS)
        self.assertEqual(data, _DATA_SAMPLE)

    def test_read_wrong_header(self):
        """ A wrong header causes "unexpected header" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'Unexpected header',
                i2cs_graph.read.read,
                    './test/data/wrong-header.csv', _SETTINGS,
            )

    def test_empty(self):
        """ An empty file causes "no data" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'No data in the file',
                i2cs_graph.read.read,
                    './test/data/empty.csv', _SETTINGS,
            )

class TestParse(unittest.TestCase):
    """ Test for data parsing functions """
    def test_parse(self):
        """ A well formed data row can be parsed """
        self.assertEqual(
                tuple(i2cs_graph.read.parse(_SAMPLE_RAW_ROW, _SETTINGS)),
                _SAMPLE_DATA_ROW
            )

    def test_short_row(self):
        """ A short row causes "row * too short" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'row ".*" too short',
                tuple, i2cs_graph.read.parse(_SAMPLE_RAW_ROW[:-2], _SETTINGS),
            )

    def test_parse_value(self):
        """ A string containing valid floating point number can be parsed """
        self.assertEqual(i2cs_graph.read.parse_value('1', 'a floating point number'), 1.0)

    def test_parse_value_empty_string(self):
        """ A NAN is returned for an empty string """
        self.assertIs(i2cs_graph.read.parse_value('', 'a floating point number'), numpy.nan)

    def test_parse_value_invalid_string(self):
        """ An invalid string causes "can't parse" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'can\'t parse ".*" as a floating point number',
                i2cs_graph.read.parse_value, 'invalid', 'a floating point number'
            )

    def test_parse_timestamp(self):
        """ A string containing valid timestamp can be parsed """
        self.assertEqual(
                i2cs_graph.read.parse_timestamp('2025-09-13 00:00:00.000000 +0000'),
                20344.0
            )

    def test_parse_timestamp_empty_string(self):
        """ An empty string causes "timestamp is empty" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'timestamp is empty',
                i2cs_graph.read.parse_timestamp, ''
            )

    def test_parse_timestamp_invalid_string(self):
        """ An invalid string causes "can't parse timestamp" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'can\'t parse timestamp',
                i2cs_graph.read.parse_timestamp, 'invalid'
            )

    def test_parse_timestamp_overflow(self):
        """ An invalid string causes "can't parse timestamp: * overflows parser" exception """
        self.assertRaisesRegex(
                i2cs_graph.error.Error, 'can\'t parse timestamp: .* overflows parser',
                i2cs_graph.read.parse_timestamp, '123456789012345678901234567890-01-01'
            )

    def test_parse_timestamp_around_dst(self):
        """ Sequential timestamps around DST transition are parsed correctly """
        # March to PDT
        t1 = i2cs_graph.read.parse_timestamp('2025-03-09 01:59:58 -0800')
        t2 = i2cs_graph.read.parse_timestamp('2025-03-09 01:59:59 -0800')
        t3 = i2cs_graph.read.parse_timestamp('2025-03-09 03:00:00 -0700')

        dt21m, dt21e = math.frexp(t2 - t1)
        dt32m, dt32e = math.frexp(t3 - t2)

        self.assertEqual((round(dt21m, 4), dt21e), (round(dt32m, 4), dt32e))

        # November to PST
        t1 = i2cs_graph.read.parse_timestamp('2025-11-02 01:59:59 -0700')
        t2 = i2cs_graph.read.parse_timestamp('2025-11-02 01:00:00 -0800')
        t3 = i2cs_graph.read.parse_timestamp('2025-11-02 01:00:01 -0800')

        dt21m, dt21e = math.frexp(t2 - t1)
        dt32m, dt32e = math.frexp(t3 - t2)

        self.assertEqual((round(dt21m, 4), dt21e), (round(dt32m, 4), dt32e))

if __name__ == '__main__':
    unittest.main()
