Yet Another Literate Python Tool
================================

YALPT is a tool to assist in literate programming.  Specifically, it is
designed for using literate programing to write interactive tutorials.


What Is Literate Programming?
-----------------------------

The term literate programing was coined by Donald Knuth (see [Wikipedia][1])
to describe a style of programming whereby documentation and information
about the code was written using normal language, generally in some markup
language, and then interspersed with actual code.  The resulting files
were then supposed to be compilable into normal programs.  In the case
of Python, this means that there should be a way to run them like normal
Python programs.


What is YALPT?
--------------

YALPT is a tool for running properly formatted literate Python files.  A
YALPT-compatible file consists of normal text interspersed with interactive
Python sessions.  These sessions should be detectable by doctest (in fact, you
can run YALPT files through doctest if you want).  Other than that, the
formatting is up to you.  YALPT comes with a formatter that takes
Markdown-formatted text and displays it using ANSI escape codes to make bold
text show up as bold, etc.  However, this is optional.

Since YALPT is based on the `doctest` and `code` modules from the Python
standard library, it behaves very similarly to the tools you already know.
In fact, YALPT will check the results of each chunk of code and warn you
if it differs from what you have written in your file.


Why YALPT?
----------

At this point, you may be asking yourself why you should use YALPT instead
of some other literate Python tool, like
[IPython notebooks](http://ipython.org/notebook.html) or
[python-literate](https://github.com/stdbrouw/python-literate).

YALPT differs from tools like python-literate because it's designed to run
the code right in an interactive session, instead of running the code and
the generating the output later.

YALPT differs from IPython notebooks in that it has a very loose format.
IPython notebooks are stored in a JSON-based format that's not particularly
easy for a human to read or write quickly.  One of the goals of YALPT is to
have files that are stand-alone, and are perfectly useful without YALPT.
This means that they should be readable and writable by humans.  Additionally
it is easy to write YALPT files that are also valid files in your markup
language of choice.  For instance, Markdown-flavored YALPT files can be passed
to a Markdown parser, so you can generate static pages as well without having
to rely on YALPT knowning how to read and output your markup and output formats
of choice.


How do I run YALPT?
-------------------

The basic invocation of YALPT is as such:

    $ run-lit.py my-file.txt

If your file is in Markdown, you can use the Markdown formatter:

    $ run-lit.py -f markdown my-file.md

By default, Markdown will drop into an interactive session after each code
block, so that you can experiment around with the results of that block before
continuing on.  To continue, simply enter two blank lines at the interactive
session (press enter twice).  If you wish to disable this, and only show an
interactive session at the end, you may pass the `--no-interactive` flag:

    $ run-lit.py my-file.txt --no-interactive

This will simply pause after each code block.  You can press enter to continue.
If you do not even want the pause, you can run YALPT with the `--no-pause`
flag:

    $ run-lit.py my-file.txt --no-pause

By default, YALPT will enable readline support for completion and history.
Completion is triggered with `Control-space`, and history is stored in your
home directory in the file `.literate-python-history`.  You can disable this
functionality with the `--no-readline` flag:

    $ run-lit.py my-file.txt --no-readline

Finally, by default YALPT will use ANSI escape codes to color the code a
different color and format error messages.  You can disable this using the
`--no-ansi` flag:

    $ run-lit.py my-file.txt --no-ansi

That's all there is to it!


I didn't read that description above, so how do I write YALPT files?
--------------------------------------------------------------------

Any file that looks like doctest-compatible interactive python sessions
interspersed between chunks of other text-based "stuff" is a YALPT-compatible
files.  As long as `doctest` can find the code chunks, so can YALPT, since
YALPT makes use of `doctest`.  You are otherwise free to use your markup
language of choice for the text parts, or even no markup at all.

However, as mentioned above, YALPT does know how to format some Markdown, but
using Markdown is by no means necessary.  If you want to write a formatter for
some other language, you can use the formatter for Markdown as a guideline, and
submit a pull request on [GitHub](https://github.com/directxman12/yalpt).


Reusing/Extending YALPT
-----------------------

The core functionality of YALPT exists in the class
`yalpt.core.LiterateInterpreter`.  This class may be subclassed to modify
functionality.

It functions much like the standard library's `code.InteractiveConsole`,
from which it inherits.

Custom formatters should implement a format method which takes a string and
returns a formatted string.


[1]: http://en.wikipedia.org/wiki/Literate_programming
