# Copyright 2014, Solly Ross (see LICENSE.txt)
# Portions Copyright Python Software Foundation
# (see COPYRIGHT.txt and PYTHON-LICENSE.txt)

# main part
import code
import contextlib
import doctest
import getpass
import linecache
import pdb
import re
import sys
import traceback
import warnings

import six

from yalpt import ansi_helper as ansi
from yalpt import formatters
from yalpt import parsers


__all__ = ["LiterateInterpreter"]


@contextlib.contextmanager
def noop_mgr(writer):
    yield writer


class LiterateInterpreter(code.InteractiveConsole):
    def __init__(self, text_formatter=formatters.NoopFormatter(),
                 code_parser=parsers.DocTestParser(), use_ansi=True,
                 use_readline=True, env_driver=None, *args, **kwargs):
        code.InteractiveConsole.__init__(self, *args, **kwargs)

        self._output_checker = doctest.OutputChecker()
        self._fakeout = doctest._SpoofOut()
        self.chunks = None
        self.exc_msg = None
        self.name = 'literate program'
        self.text_formatter = text_formatter
        self.code_parser = code_parser
        self.use_ansi = use_ansi
        self.pause = True
        self.interactive = True

        if use_readline:
            self._readline = __import__('readline')
            self._add_readline()
        else:
            self._readline = None

        self._env_driver = env_driver

        self._correct_path()

    def runfunction(self, func):
        self.runcode(six.get_function_code(func))

    def _correct_path(self):
        def correct_path():
            import sys
            if '' not in sys.path:
                sys.path.insert(0, '')
            del sys

        self.runfunction(correct_path)

    def _add_readline(self):
        self.locals['__console_locals__'] = self.locals
        self.locals['readline'] = self._readline

        def add_readline():
            # add support for completion
            import atexit
            import os
            import readline
            import rlcompleter

            completer = rlcompleter.Completer(__console_locals__)  # noqa
            readline.set_completer(completer.complete)

            # tab completion
            readline.parse_and_bind('Control-space: complete')
            # history file
            histfile = os.path.join(os.environ['HOME'],
                                    '.literate-python-history')
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            atexit.register(readline.write_history_file, histfile)
            del os, histfile, readline, rlcompleter

        self.runfunction(add_readline)

        del self.locals['__console_locals__']
        del self.locals['readline']

    def _interact_once(self, more):
        try:
            if more:
                prompt = sys.ps2
            else:
                prompt = sys.ps1
            try:
                line = self.raw_input(prompt)
                # Can be None if sys.stdin was redefined
                encoding = getattr(sys.stdin, "encoding", None)
                if encoding and not isinstance(line, six.text_type):
                    line = line.decode(encoding)
            except EOFError:
                self.write("\n")
                return (False, None)
            else:
                if len(line) == 0:
                    blank = True
                else:
                    blank = False
                more = self.push(line)
        except KeyboardInterrupt:
            self.write("\nKeyboardInterrupt\n")
            self.resetbuffer()
            more = False
            blank = False

        return (blank, more)

    # BEGIN FROM PYTHON STD LIB
    # (extracted from the doctest module, made slight changes to the
    # filename RE, and refactored _capture_output into its own method)
    __LINECACHE_FILENAME_RE = re.compile(r'<literate '
                                         r'(?P<name>.+)'
                                         r'\[(?P<chunknum>\d+)\]>$')

    def _patched_linecache_getlines(self, filename, module_globals=None):
        m = self.__LINECACHE_FILENAME_RE.match(filename)
        if m and m.group('name') == self.name:
            chunk = self.chunks[int(m.group('chunknum'))]
            source = chunk.source
            if isinstance(source, six.text_type):
                source = source.encode('ascii', 'backslashreplace')
            return source.splitlines(True)
        else:
            return self.save_linecache_getlines(filename, module_globals)

    @contextlib.contextmanager
    def _capture_output(self):
        save_stdout = sys.stdout
        sys.stdout = self._fakeout

        # set up pdb to work properly
        save_set_trace = pdb.set_trace
        self.debugger = doctest._OutputRedirectingPdb(save_stdout)
        self.debugger.reset()
        pdb.set_trace = self.debugger.set_trace
        self.save_linecache_getlines = linecache.getlines
        linecache.getlines = self._patched_linecache_getlines
        save_displayhook = sys.displayhook
        sys.displayhook = sys.__displayhook__

        try:
            yield sys.stdout
        finally:
            sys.stdout = save_stdout
            pdb.set_trace = save_set_trace
            linecache.getlines = self.save_linecache_getlines
            sys.displayhook = save_displayhook
    # END FROM PYTHON STD LIB

    def _process_code_line(self, line, res, more):
        if self._readline is not None:
            self._readline.add_history(line)

        if more:
            self.write(sys.ps2)
        else:
            self.write(sys.ps1)

        if self.use_ansi:
            self.write(ansi.with_codes(line, 38, 5, 0xdf))
        else:
            self.write(line)

        self.write("\n")
        with self._capture_output() as output:
            more = self.push(line)

            res += output.getvalue()
            output.truncate(0)

        exc = self.exc_msg
        self.exc_msg = None
        return (res, exc, more)

    def _format_tb(self):
        try:
            extype, value, tb = sys.exc_info()
            sys.last_type = extype
            sys.last_value = value
            sys.last_traceback = tb
            res = traceback.format_exception_only(extype, value)
        finally:
            tb = None

        if res:
            return res[-1]

    def showtraceback(self):
        try:
            extype, value, tb = sys.exc_info()
            sys.last_type = extype
            sys.last_value = value
            sys.last_traceback = tb
            tblist = traceback.extract_tb(tb)
            del tblist[:1]
            lst = traceback.format_list(tblist)
            if lst:
                lst.insert(0, "Traceback (most recent call last):\n")
            exc_msg = traceback.format_exception_only(extype, value)
            lst[len(lst):] = exc_msg
        finally:
            tblist = tb = None

        if self.filename.startswith("<literate "):
            self._fakeout.write(''.join(lst))
        else:
            if sys.excepthook is sys.__excepthook__:
                self.write(''.join(lst))
            else:
                sys.excepthook(extype, value, tb)

        self.exc_msg = ''.join(exc_msg)

    def _run_code(self, chunk, chunk_ind, pause=True):
        self.filename = "<literate {name}[{num}]>".format(name=self.name,
                                                          num=chunk_ind)
        more = False
        res = ""
        lines = chunk.source.split("\n")
        for line in lines[:-1]:
            res, exc, more = self._process_code_line(line, res, more)

        if more:
            res, exc, more = self._process_code_line(lines[-1], res, more)

        if self.use_ansi:
            mgr = ansi.BoxMaker(self)
        else:
            mgr = noop_mgr(self)

        if chunk.want is not None or chunk.exc_msg is not None:
            if len(res) > 0 or exc is not None:
                # compare to the expected output
                # TODO(sross): convert options to optionsflags
                optionsflags = 0

                checker = self._output_checker
                if exc is None:
                    same = self._output_checker.check_output(chunk.want,
                                                             res, 0)
                    if not same:
                        self.write('\n')
                        with mgr as maker:
                            maker.write('Warning, output different from '
                                        'expected:\n')
                            maker.write('================================'
                                        '========\n\n')
                            diff = checker.output_difference(chunk, res,
                                                             optionsflags)
                            maker.write(diff)
                        self.write('\n')
                    else:
                        self.write(res)
                elif chunk.exc_msg is None:
                    self.write('\n')
                    with mgr as maker:
                        maker.write('Warning, unexpected exception:\n')
                        maker.write('==============================\n\n')
                        maker.write(exc)
                    self.write('\n')
                else:
                    same_ex = checker.check_output(chunk.exc_msg,
                                                   exc, optionsflags)
                    if not same_ex:
                        self.write('\n')
                        with mgr as maker:
                            maker.write('Warning, exception different from '
                                        'expected:\n')
                            maker.write('=================================='
                                        '=========\n\n')
                            diff = checker.output_difference(chunk, res,
                                                             optionsflags)
                            maker.write(diff)
                        self.write('\n')
                    else:
                        self.write(res)
        else:
            if exc is not None:
                self.write('\n')
                with mgr as maker:
                    maker.write('Warning, unexpected exception:\n')
                    maker.write('==============================\n\n')
                    maker.write(exc)
                self.write('\n')
            else:
                self.write(res)

        if not self.pause:
            self.write(sys.ps1 + '\n')

    def no_echo_input(self, prompt):
        with warnings.catch_warnings():
            res = getpass.getpass(prompt)
        return res

    def interact(self, lit_string, name, pause=True, interactive=True):
        self.name = name
        self.pause = pause
        self.interactive = interactive

        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "

        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "

        try:
            sys.ps3
        except AttributeError:
            sys.ps3 = '>>> '

        if self._env_driver is not None:
            extra_locals = self._env_driver.setup()
            self.locals.update(extra_locals)
            extra_banner = self._env_driver.banner
            driver_text = " ({0})".format(self._env_driver.DRIVER_NAME)
        else:
            extra_banner = ""
            driver_text = ""

        cprt = ('Type "help", "copyright", "credits" or "license" for '
                'more information about Python.')
        self.write("Literate Python Shell{driver_text}\nPython {ver} "
                   "on {platform}\n{cprt}\n"
                   "{extra_banner}\n\n".format(driver_text=driver_text,
                                               ver=sys.version,
                                               platform=sys.platform,
                                               cprt=cprt,
                                               extra_banner=extra_banner))

        if not interactive and pause:
            self.write('Press enter to continue after a code block\n\n')

        try:
            parser = self.code_parser
            start = True
            self.chunks = list(parser.parse(lit_string, name))
            for chunk_ind, chunk in enumerate(self.chunks):
                if isinstance(chunk, parsers.CodeChunk):
                    self._run_code(chunk, chunk_ind)
                elif not chunk:
                    continue
                else:
                    if not start and pause and interactive:
                        self.filename = "<stdin>"
                        more = False
                        blanks = 0
                        while blanks < 2:
                            blank, more = self._interact_once(more)

                            if blank:
                                blanks += 1
                            else:
                                blanks = 0

                            if more is None:
                                return

                        # reset exc_msg so it doesn't get
                        # raised after the next code block
                        self.exc_msg = None
                    elif not start and pause:
                        self.no_echo_input(sys.ps3)

                    self.write(self.text_formatter.format(chunk))

                start = False

            complete_msg = ("\n{file} complete! Continuing to interactive "
                            "console...\n\n".format(file=self.name))

            if self.use_ansi:
                self.write(ansi.with_codes(complete_msg, 1))
            else:
                self.write(complete_msg)

            self.filename = "<stdin>"
            self.locals['con'] = self
            more = False
            while more is not None:
                blank, more = self._interact_once(more)
        finally:
            if self._env_driver is not None:
                self._env_driver.teardown()
