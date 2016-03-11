#! /usr/bin/env python
# Copyright 2014, Solly Ross (see LICENSE.txt)
from __future__ import print_function

import argparse
import os.path
import sys

import pkg_resources as pkgres

from yalpt import core


parser = argparse.ArgumentParser()
parser.formatter_class = argparse.RawDescriptionHelpFormatter
parser.usage = "%(prog)s [OPTION]... file"
parser.description = "Yet Another Literate Python Tool"
parser.epilog = """

YAPLT is a tool for interacting with documentation
interspersed with python code.  Unlike other literate
python tools, most of which are designed for producing
static documentation, YALPT is designed for writing
interactive tutorials.

By default, YALPT will drop into an interactive session
after each code block, allowing you to experiment around
with the results of the last block of code.  Once you are
done experimenting, simply enter two blank lines,
and YALPT will continue with the file.

Python code should be written so that it would be detectable
by the doctest module.  This means that code samples should
look like interactive python sessions.

Other than that, the format can vary.  You are free to use
your own style for the documentation, although YALPT comes
with a built-in formatter that renders a subset of Markdown
with ANSI escape codes, so it looks nice in your terminal.
"""

parser.add_argument('file',
                    help='The YALPT literate python file to run')
parser.add_argument('--no-pause', action='store_false', dest='pause',
                    default=True,
                    help="Don't pause after every code block.  "
                         "Implies --no-interactive")
parser.add_argument('--no-interactive', action='store_false',
                    dest='interactive', default=True,
                    help="Don't drop to an interactive console "
                         "after every code block")
parser.add_argument('-f', '--format', default=None,
                    help="Format the text portions using ANSI "
                         "escape codes.  Currently accepts 'md' and 'none'. "
                         "YALPT will attempt to automatically set this based "
                         "on file extension.")
parser.add_argument('-p', '--code-parser', default='doctest',
                    help="Which method was used to embed code samples in the "
                         "document.  Currently accepts 'doctest' and "
                         "'markdown'.")
parser.add_argument('--no-readline', dest='readline', action='store_false',
                    default=True,
                    help="Don't import readline for completion and history")
parser.add_argument('--no-ansi', dest='ansi', action='store_false',
                    default=True,
                    help="Don't use ANSI escape codes to provide color and "
                         "formatting.  Will not work with --format.")
parser.add_argument('-e, --env-driver', dest='env_driver', default=None,
                    help="Use the given env driver to set up the environment"
                         "in which the code executes.  Use [] to pass a "
                         "parameter.")

args = parser.parse_args()

filename = os.path.basename(args.file)

# code parser
parsers = pkgres.iter_entry_points('yalpt.parsers', args.code_parser)

try:
    code_parser_cls_loader = next(parsers)
except StopIteration:
    sys.exit("Could not load code parser %s" % args.code_parser)


code_parser = code_parser_cls_loader.load()()

# text formatter
if not args.ansi and args.format:
    sys.exit("Cannot use a formatter without ANSI escape code support!")

if args.format is None:
    if '.' in filename:
        args.format = filename.rsplit('.', 1)[-1]
    else:
        args.format = 'none'

if not args.ansi:
    args.format = 'none'

formatters = pkgres.iter_entry_points('yalpt.formatters', args.format)

try:
    formatter_cls_loader = next(formatters)
except StopIteration:
    print("Warning: cannot load formatter for the .%s extension -- "
          "no formatters found." % args.format, file=sys.stderr)

    formatter_cls_loader = next(pkgres.iter_entry_points('yalpt.formatters',
                                                         'none'))

text_formatter = formatter_cls_loader.load()()


env_driver = None
if args.env_driver:
    if '[' in args.env_driver:
        bracket_pos = args.env_driver.index('[')
        env_driver_name = args.env_driver[:bracket_pos]
        env_driver_args = [args.env_driver[bracket_pos + 1:-1]]
    else:
        env_driver_name = args.env_driver
        env_driver_args = []

    env_drivers = pkgres.iter_entry_points('yalpt.env_drivers',
                                           args.env_driver)
    try:
        env_driver_loader = next(env_drivers)
        env_driver = env_driver_loader.load()(*env_driver_args)
    except StopIteration:
        sys.exit("Error: cannot load env driver %s -- no such "
                 "env driver found" % args.env_driver)
        env_driver = None

interpreter = core.LiterateInterpreter(text_formatter=text_formatter,
                                       code_parser=code_parser,
                                       use_ansi=args.ansi,
                                       use_readline=args.readline,
                                       env_driver=env_driver)
with open(args.file) as f:
    interpreter.interact(f.read(), filename,
                         pause=args.pause, interactive=args.interactive)
