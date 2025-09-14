""" The submodule provides an entry point for the script """

import sys
import argparse

from .error import Error
from .read import read, ALS_DEFAULT_RESOLUTION

def make_args_parser() -> argparse.ArgumentParser:
    """ Creates an argument parser """
    parser = argparse.ArgumentParser(description='I2C Sensors Visualizing Script')
    parser.add_argument('data', type=str, nargs=1,
                        help='file with CSV formatted data from i2cs-test script',
                        metavar='PATH')
    parser.add_argument('--als-resolution', type=float, default=ALS_DEFAULT_RESOLUTION,
                        help= 'resolution configured for ambient light sensor during measurements '
                             f'(default: {ALS_DEFAULT_RESOLUTION})',
                        metavar='N')
    return parser

def main() -> int:
    """ Entry point for the script """
    args = make_args_parser().parse_args()

    try:
        data = read(args.data[0], args)
        print(f'Got {len(data[0])} data points')
    except Error as e:
        print(f'{e}. Exiting...', file=sys.stderr)
        return 1

    return 0
