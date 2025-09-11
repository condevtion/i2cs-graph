""" The submodule provides an entry point for the script """

import sys
import argparse

from .error import Error

def make_args_parser() -> argparse.ArgumentParser:
    """ Creates an argument parser """
    parser = argparse.ArgumentParser(description='I2C Sensors Visualizing Script')
    parser.add_argument('data', type=str, nargs=1,
                        help='file with CSV formatted data from i2cs-test script',
                        metavar='PATH')
    return parser

def main() -> int:
    """ Entry point for the script """
    args = make_args_parser().parse_args()

    try:
        print(f'args: {args!r}')
    except Error as e:
        print(f'{e}. Exiting...', file=sys.stderr)
        return 1

    return 0
