""" The submodule provides an entry point for the script """

import sys
import argparse
import time

from .error import Error
from .read import read, ALS_SENSITIVITY, ALS_DEFAULT_RESOLUTION
from .scale import prescale
from .combined import plot_combined
from .split import plot_split

def make_args_parser() -> argparse.ArgumentParser:
    """ Creates an argument parser """
    parser = argparse.ArgumentParser(description='I2C Sensors Visualizing Script')
    parser.add_argument('data', type=str, nargs=1,
                        help='file with CSV formatted data from i2cs-test script',
                        metavar='PATH')
    parser.add_argument('--combined', action='store_true', default=False,
                        help='plot combined chart (default: split)')
    parser.add_argument('--als-resolution', type=int,
                        choices=ALS_SENSITIVITY.keys(), default=ALS_DEFAULT_RESOLUTION,
                        help= 'resolution configured for ambient light sensor during measurements '
                             f'(16 - 20, default: {ALS_DEFAULT_RESOLUTION})',
                        metavar='N')
    return parser

def main() -> int:
    """ Entry point for the script """
    args = make_args_parser().parse_args()

    try:
        start = time.monotonic()
        data = read(args.data[0], args)
        print(f'Got {len(data[0])} data points in {time.monotonic() - start:.1f}s')

        data_set = prescale(data)
        if args.combined:
            plot_combined(data_set)
        else:
            plot_split(data_set)
    except Error as e:
        print(f'{e}. Exiting...', file=sys.stderr)
        return 1

    return 0
