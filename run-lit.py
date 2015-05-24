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
                         "document.  Currently only accepts 'doctest")
parser.add_argument('--no-readline', dest='readline', action='store_false',
                    default=True,
                    help="Don't import readline for completion and history")
parser.add_argument('--no-ansi', dest='ansi', action='store_false',
                    default=True,
                    help="Don't use ANSI escape codes to provide color and "
                         "formatting.  Will not work with --format.")

args = parser.parse_args()

filename = os.path.basename(args.file)

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

interpreter = core.LiterateInterpreter(text_formatter=text_formatter,
                                       use_ansi=args.ansi,
                                       use_readline=args.readline)
with open(args.file) as f:
    interpreter.interact(f.read(), filename,
                         pause=args.pause, interactive=args.interactive)
