""" Contains tests for the scale submodule """

import unittest

import numpy

from helper import SECOND, UTC, gen_seq

import i2cs_graph.scale
import i2cs_graph.sequencer
import i2cs_graph.read

_MIN_COLOR_18 = 0.5/(2**18-1)
_TS = (20344, 20344 + SECOND, 20344 + 2*SECOND, 20344 + 3*SECOND)
_NANS = (numpy.nan, numpy.nan, numpy.nan, numpy.nan)
_RESAMPLED_NANS = i2cs_graph.scale.ResampledValue(
        (numpy.nan, numpy.nan), (numpy.nan, numpy.nan), (numpy.nan, numpy.nan)
    )
_DATA_SAMPLE = (
    _TS,
    i2cs_graph.read.Data(
        i2cs_graph.read.Pressure(
            (1000.0, 990.0, 980.0, 970.0),
            (0.0, 1.0, 2.0, 3.0)
        ),
        i2cs_graph.read.RelativeHumidity(
            (50.0, 49.0, 48.0, 47.0),
            (0.0, 1.0, 2.0, 3.0)
        ),
        i2cs_graph.read.AmbientLight(
            (18.0, 9.0, 6.0, 3.0),
            (7000.0, 15000.0, 23000.0, 47000.0),
            (6000.0, 14000.0, 22000.0, 46000.0),
            i2cs_graph.read.Color(
                (25.0, 50.0, 75.0, 100.0),
                (25.0, 50.0, 75.0, 100.0),
                (25.0, 50.0, 75.0, 100.0)
            )
        )
    )
)

_DATA_SAMPLE_PART_NAN = (
    _TS,
    i2cs_graph.read.Data(
        i2cs_graph.read.Pressure(
            (1000.0, numpy.nan, 990.0, numpy.nan),
            (0.0, numpy.nan, 1.0, numpy.nan)
        ),
        i2cs_graph.read.RelativeHumidity(
            (50.0, numpy.nan, 49.0, numpy.nan),
            (0.0, numpy.nan, 1.0, numpy.nan)
        ),
        i2cs_graph.read.AmbientLight(
            (18.0, numpy.nan, 9.0, numpy.nan),
            (7000.0, numpy.nan, 23000.0, numpy.nan),
            (6000.0, numpy.nan, 22000.0, numpy.nan),
            i2cs_graph.read.Color(
                (25, numpy.nan, 75, numpy.nan),
                (25, numpy.nan, 75, numpy.nan),
                (25, numpy.nan, 75, numpy.nan)
            )
        )
    )
)

_DATA_SAMPLE_ALL_NAN = (
    _TS,
    i2cs_graph.read.Data(
        i2cs_graph.read.Pressure(_NANS, _NANS),
        i2cs_graph.read.RelativeHumidity(_NANS, _NANS),
        i2cs_graph.read.AmbientLight(
            _NANS, _NANS, _NANS,
            i2cs_graph.read.Color(_NANS, _NANS, _NANS)
        )
    )
)

class TestPrescale(unittest.TestCase):
    """ Tests for data downsampling functions """
    def test_span_str(self):
        """ Different timespans can be converted to correct strings """

        dt = 1*7 + 1 + (1 + (1 + (1 + 100/1000)/60)/60)/24
        self.assertEqual(
                i2cs_graph.scale.span_str(dt),
                '1w 1d 01h 01m 01.100s'
            )

        dt = 1 + (1 + (1 + (1 + 100/1000)/60)/60)/24
        self.assertEqual(
                i2cs_graph.scale.span_str(dt),
                '1d 01h 01m 01.100s'
            )

        dt = (1 + (1 + (1 + 100/1000)/60)/60)/24
        self.assertEqual(
                i2cs_graph.scale.span_str(dt),
                '01h 01m 01.100s'
            )

        dt = ((1 + (1 + 100/1000)/60)/60)/24
        self.assertEqual(
                i2cs_graph.scale.span_str(dt),
                '01m 01.100s'
            )

        dt = (((1 + 100/1000)/60)/60)/24
        self.assertEqual(
                i2cs_graph.scale.span_str(dt),
                '01.100s'
            )

        dt = 0
        self.assertEqual(
                i2cs_graph.scale.span_str(dt),
                '00.000s'
            )

    def test_make_overview(self):
        """ Produces a two point "overview" for a long enough data sample """
        self.assertEqual(
                i2cs_graph.scale.make_overview(_DATA_SAMPLE),
                (
                    (20344, 20344 + 3*SECOND),
                    i2cs_graph.scale.ResampledData(
                        i2cs_graph.scale.ResampledPressure(
                            i2cs_graph.scale.ResampledValue(
                                (995.0, 975.0), (990.0, 970.0), (1000.0, 980.0),
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (0.5, 2.5), (0.0, 2.0), (1.0, 3.0),
                            ),
                        ),
                        i2cs_graph.scale.ResampledRelativeHumidity(
                            i2cs_graph.scale.ResampledValue(
                                (49.5, 47.5), (49.0, 47.0), (50.0, 48.0),
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (0.5, 2.5), (0.0, 2.0), (1.0, 3.0),
                            ),
                        ),
                        i2cs_graph.scale.ResampledAmbientLight(
                            i2cs_graph.scale.ResampledValue(
                                (13.5, 4.5), (9.0, 3.0), (18.0, 6.0),
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (11000.0, 35000.0), (7000.0, 23000.0), (15000.0, 47000.0),
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (10000.0, 34000.0), (6000.0, 22000.0), (14000.0, 46000.0),
                            ),
                            i2cs_graph.scale.ResampledColor(
                                (25.0, 100.0),
                                (25.0, 100.0),
                                (25.0, 100.0),
                            ),
                        ),
                    )
                )
            )

        self.assertEqual(
                i2cs_graph.scale.make_overview(_DATA_SAMPLE_PART_NAN),
                (
                    (20344, 20344 + 3*SECOND),
                    i2cs_graph.scale.ResampledData(
                        i2cs_graph.scale.ResampledPressure(
                            i2cs_graph.scale.ResampledValue(
                                (1000.0, 990.0), (1000.0, 990.0), (1000.0, 990.0)
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)
                            ),
                        ),
                        i2cs_graph.scale.ResampledRelativeHumidity(
                            i2cs_graph.scale.ResampledValue(
                                (50.0, 49.0), (50.0, 49.0), (50.0, 49.0)
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)
                            ),
                        ),
                        i2cs_graph.scale.ResampledAmbientLight(
                            i2cs_graph.scale.ResampledValue(
                                (18.0, 9.0), (18.0, 9.0), (18.0, 9.0),
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (7000.0, 23000.0), (7000.0, 23000.0), (7000.0, 23000.0),
                            ),
                            i2cs_graph.scale.ResampledValue(
                                (6000.0, 22000.0), (6000.0, 22000.0), (6000.0, 22000.0),
                            ),
                            i2cs_graph.scale.ResampledColor(
                                (25.0, 75.0),
                                (25.0, 75.0),
                                (25.0, 75.0),
                            ),
                        ),
                    )
                )
            )

        self.assertEqual(
                i2cs_graph.scale.make_overview(_DATA_SAMPLE_ALL_NAN),
                (
                    (20344, 20344 + 3*SECOND),
                    i2cs_graph.scale.ResampledData(
                        i2cs_graph.scale.ResampledPressure(
                            _RESAMPLED_NANS, _RESAMPLED_NANS
                        ),
                        i2cs_graph.scale.ResampledRelativeHumidity(
                            _RESAMPLED_NANS, _RESAMPLED_NANS
                        ),
                        i2cs_graph.scale.ResampledAmbientLight(
                            _RESAMPLED_NANS, _RESAMPLED_NANS, _RESAMPLED_NANS,
                            i2cs_graph.scale.ResampledColor(
                                (numpy.nan, numpy.nan),
                                (numpy.nan, numpy.nan),
                                (numpy.nan, numpy.nan),
                            )
                        ),
                    )
                )
            )

    def test_downsample(self):
        """ A data sequence can be downsampled """
        t, y = zip(*gen_seq(8, (20089.0, 4*SECOND), (0.0, 1)))

        self.maxDiff = None
        self.assertEqual(
                tuple(i2cs_graph.scale.downsample(
                    (t, i2cs_graph.read.Data(
                        i2cs_graph.read.Pressure(y, y),
                        i2cs_graph.read.RelativeHumidity(y, y),
                        i2cs_graph.read.AmbientLight(y, y, y, i2cs_graph.read.Color(y, y, y))
                    )),
                    lambda x: i2cs_graph.sequencer.make_time_sequence_15s(x, UTC)
                )),
                (
                    (
                        20089.0,
                        0.5, 0.0, 1.0, 0.5, 0.0, 1.0,
                        0.5, 0.0, 1.0, 0.5, 0.0, 1.0,
                        0.5, 0.0, 1.0, 0.5, 0.0, 1.0, 0.5, 0.0, 1.0, 0.5, 0.5, 0.5,
                    ),
                    (
                        20089.000173611108,
                        3.5, 2.0, 5.0, 3.5, 2.0, 5.0,
                        3.5, 2.0, 5.0, 3.5, 2.0, 5.0,
                        3.5, 2.0, 5.0, 3.5, 2.0, 5.0, 3.5, 2.0, 5.0, 3.0, 3.0, 3.0,

                    ),
                    (
                        20089.000347222223,
                        6.5, 6.0, 7.0, 6.5, 6.0, 7.0,
                        6.5, 6.0, 7.0, 6.5, 6.0, 7.0,
                        6.5, 6.0, 7.0, 6.5, 6.0, 7.0, 6.5, 6.0, 7.0, 6.5, 6.5, 6.5,
                    ),
                )
            )

    def test_prescale(self):
        """ A prescaled data set can be created for the given data sequence """

        # Short sequence
        t, y = zip(*gen_seq(8, (20089.0, SECOND), (0.0, 1)))
        orig = (t, i2cs_graph.read.Data(
                i2cs_graph.read.Pressure(y, y),
                i2cs_graph.read.RelativeHumidity(y, y),
                i2cs_graph.read.AmbientLight(y, y, y, i2cs_graph.read.Color(y, y, y))
            ))
        self.assertEqual(
                i2cs_graph.scale.prescale(orig),
                i2cs_graph.scale.DataSet(
                    orig,
                    {},
                    None,
                )
            )

        t, y = zip(*gen_seq(10000, (20089.0, SECOND), (0.0, 1)))
        orig = (t, i2cs_graph.read.Data(
                i2cs_graph.read.Pressure(y, y),
                i2cs_graph.read.RelativeHumidity(y, y),
                i2cs_graph.read.AmbientLight(y, y, y, i2cs_graph.read.Color(y, y, y))
            ))

        data_set = i2cs_graph.scale.prescale(orig)
        self.assertIsInstance(data_set, i2cs_graph.scale.DataSet)
        self.assertEqual(data_set.orig, orig)

        self.assertEqual(tuple(data_set.scaled.keys()), (15/60/60/24, 1/60/24))

        sc15s = data_set.scaled[15/60/60/24]
        pts = len(sc15s[0])
        self.assertEqual(pts, round(10000/15) + 1)
        self.assertEqual(
                (len(sc15s[1].p.p.avg), len(sc15s[1].p.p.mn), len(sc15s[1].p.p.mx)),
                (pts, pts, pts)
            )
        self.assertEqual(
                (len(sc15s[1].p.t.avg), len(sc15s[1].p.t.mn), len(sc15s[1].p.t.mx)),
                (pts, pts, pts)
            )
        self.assertEqual(
                (len(sc15s[1].rh.rh.avg), len(sc15s[1].rh.rh.mn), len(sc15s[1].rh.rh.mx)),
                (pts, pts, pts)
            )
        self.assertEqual(
                (len(sc15s[1].rh.t.avg), len(sc15s[1].rh.t.mn), len(sc15s[1].rh.t.mx)),
                (pts, pts, pts)
            )
        self.assertEqual(
                (len(sc15s[1].al.gain.avg), len(sc15s[1].al.gain.mn), len(sc15s[1].al.gain.mx)),
                (pts, pts, pts)
            )
        self.assertEqual(
                (len(sc15s[1].al.al.avg), len(sc15s[1].al.al.mn), len(sc15s[1].al.al.mx)),
                (pts, pts, pts)
            )
        self.assertEqual(
                (len(sc15s[1].al.ir.avg), len(sc15s[1].al.ir.mn), len(sc15s[1].al.ir.mx)),
                (pts, pts, pts)
            )

        sc1m = data_set.scaled[1/60/24]
        self.assertEqual(len(sc1m[0]), round(10000/60) + 1)

        rval = i2cs_graph.scale.ResampledValue((2499.5, 7499.5), (0.0, 5000.0), (4999.0, 9999.0))
        self.assertEqual(data_set.overview, (
                (20089.0, 20089.115729166668),
                i2cs_graph.scale.ResampledData(
                    i2cs_graph.scale.ResampledPressure(rval, rval),
                    i2cs_graph.scale.ResampledRelativeHumidity(rval, rval),
                    i2cs_graph.scale.ResampledAmbientLight(
                        rval, rval, rval,
                        i2cs_graph.scale.ResampledColor(
                            (0.0, 9999.0),
                            (0.0, 9999.0),
                            (0.0, 9999.0)
                        )
                    )
                )
            ))

if __name__ == '__main__':
    unittest.main()
