# Copyright 2014, Solly Ross (see LICENSE.txt)
import six


_ESC = '\x1b'
_CSI = _ESC + '['
_SET_FONT_G1 = _ESC + ')'
_SAVE_STATE = _ESC + '7'
_LOAD_STATE = _ESC + '8'

_SHIFT_OUT = '\x0E'
_SHIFT_IN = '\x0F'

_GRAPHICS_FONT = '0'


def with_codes(text, *codes):
    str_codes = [six.text_type(code) for code in codes]
    return _CSI + (';'.join(str_codes)) + 'm' + text + _CSI + '0m'


class BoxMaker(object):
    def __init__(self, to, padding=1):
        self.output = to
        self.padding = padding

    def __enter__(self):
        self.curr_len = 0
        self.width = 0
        self.buff = ['']
        return self

    def _output_line(self, line):
        self.output.write(_SHIFT_OUT + 'x' + _SHIFT_IN)
        self.output.write(' ' * self.padding)
        self.output.write(line)
        if len(line) < self.unpadded_width:
            self.output.write(' ' * (self.unpadded_width - len(line)))
        self.output.write(' ' * self.padding)
        self.output.write(_SHIFT_OUT + 'x' + _SHIFT_IN + '\n')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.output.write(_SAVE_STATE)
        self.output.write(_SET_FONT_G1 + _GRAPHICS_FONT)

        self.unpadded_width = self.width
        self.width += self.padding * 2

        # suppress a final extraneous newline
        if self.buff[-1] == '':
            del self.buff[-1]

        # top
        self.output.write(_SHIFT_OUT + 'l' + ('q' * self.width) + 'k' +
                          _SHIFT_IN + '\n')

        for i in six.moves.range(self.padding):
            self._output_line('')

        for line in self.buff:
            self._output_line(line)

        for i in six.moves.range(self.padding):
            self._output_line('')

        # bottom
        self.output.write(_SHIFT_OUT + 'm' + ('q' * self.width) + 'j' +
                          _SHIFT_IN + '\n')
        self.output.write(_LOAD_STATE)

        return False

    def write(self, contents):
        lines = contents.split('\n')
        if len(lines) > 1:
            self.buff[-1] += lines[0]
            self.curr_len += len(lines[0])
            if self.curr_len > self.width:
                self.width = self.curr_len

            for line in lines[1:]:
                self.curr_len = len(line)
                if self.curr_len > self.width:
                    self.width = self.curr_len

                self.curr_len = 0

            self.buff.extend(lines[1:])
        else:
            # no newline
            self.buff[-1] += lines[0]
            self.curr_len += len(lines[0])
