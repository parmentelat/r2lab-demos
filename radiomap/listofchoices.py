#!/usr/bin/env python3

"""
This is an extension to the argparse ecosystem

Purpose is to enable the creation of CLI options that would behave like
action=append, but with a check on choices

(*) accumulative : *dest* holds a list of strings (might be extensible to support types)
(*) restrictive : all elements in the list must be in *choices*

In practical terms, we want to specify one or several values for a parameter
that is itself constrained, like an antenna mask that must be among '1', '3' and '7'

As of this writing, it is possible to write a code that uses
action=append, choices=['a', 'b', 'c'] and default=['a', 'b']
but then defaults are always returned...
"""

import argparse

class ListOfChoices(argparse.Action):

    """
    Use with e.g.
        parser.add_argument(choices=('1', '2', '3', '4'), default=['1', '2'],
                            typeaction=ListOfChoices)
    """

    def __init__(self, *args, **kwds):
        self.result = []
        super().__init__(*args, **kwds)

    def __call__(self, parser, namespace, value, option_string=None):
        self.result.append(value)
        setattr(namespace, self.dest, self.result)

#################### unit test
if __name__ == '__main__':
    def test1():
        """
        ListOfChoices micro-test
        """
        def new_parser():
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser.add_argument("-a", "--antenna-mask", default=['1', '1'],
                                choices=['1', '3', '7', '11'],
                                action=ListOfChoices,
                                help="specify antenna mask for each node")
            return parser

        print(new_parser().parse_args([]))
        print(new_parser().parse_args(['-a', '1']))
        print(new_parser().parse_args(['-a', '1', '-a', '3']))
        print(new_parser().parse_args(['-a', '1', '-a', '3', '-a', '11']))
        print(new_parser().parse_args())

    test1()
