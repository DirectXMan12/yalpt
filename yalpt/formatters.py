# Copyright 2014, Solly Ross (see LICENSE.txt)
import re

import six

from yalpt import ansi_helper as ansi


class NoopFormatter(object):
    def format(self, s):
        return s


class MarkdownFormatter(object):
    FORMAT_CODES = {'\x01': 1,
                    '\x04': 3,
                    '\x05': 7,
                    '\x1C': [48, 5, 0xea],
                    '\x06': 4,
                    '\x07': 3}

    FORMAT_CHARS = {'\x01': u'**',
                    '\x04': u'*',
                    '\x05': u'==',
                    '\x06': u'_',
                    '\x1C': u' ',  # use spaces instead of '`'
                    '\x07': u'~~'}

    # BOLD MUST BE MATCHED FIRST, AND SUBSTITUTED OUT
    # TODO(sross): this will miss the case of *a*, etc

    # bold: **text** --> \x01
    BOLD_RE = re.compile(r'(?<!\\)\*\*(?P<text>[^ *].*?[^ \\])\*\*')

    # italics: *text* --> \x04
    ITALICS_RE = re.compile(r'(?<!\\)\*(?P<text>[^ ].*?[^ \\])\*')

    # highlight: ==text== --> \x05
    HIGHLIGHT_RE = re.compile(r'(?<!\\)==(?P<text>[^ =].*?[^ \\])==')

    # underline: _text_ --> \x06
    UNDERLINE_RE = re.compile(r'(?<!\\|\w)_(?P<text>[^ ].*?[^ \\])_')

    # strikethrough: ~~text~~ --> \x07
    STRIKETHROUGH_RE = re.compile(r'(?<!\\)~~(?P<text>[^ ].*?[^ \\])~~')

    # code: `text`
    CODE_RE = re.compile(r'`(?P<text>.+?)`')

    AFTER_RE = re.compile('\x02(?P<code>.)(?P<text>.+?)\x03')

    HEADER_RE1 = re.compile(r'^(?P<start>#+) (?P<name>.+?)(?P<end> #+)?$',
                            re.MULTILINE)
    HEADER_RE2 = re.compile(r'^(?P<text>.+)\n(?P<underline>(==+)|(--+))$',
                            re.MULTILINE)

    def _add_ansi_formatting(self, match):
        sub_code = match.group('code')

        if sub_code == '\x1C':
            # deal with the special code blocks thing
            block_num = int(match.group('text'))
            inner_text = self.code_blocks[block_num]
        else:
            inner_text = match.group('text')

        codes = self.FORMAT_CODES[sub_code]
        if isinstance(codes, int):
            codes = [codes]
        chars = self.FORMAT_CHARS[sub_code]
        text = chars + inner_text + chars

        return ansi.with_codes(text, *codes)

    def _remove_code_block(self, match):
        self.code_blocks.append(match.group('text'))
        return '\x02\x1C' + six.text_type(len(self.code_blocks)-1) + '\x03'

    def format(self, s):
        self.code_blocks = []

        # first, temporarily remove any code blocks,
        # as we don't want them formatted
        s = self.CODE_RE.sub(self._remove_code_block, s)

        # first find bold, and then italic, then the rest
        s = self.BOLD_RE.sub('\x02\x01\\g<text>\x03', s)
        s = self.ITALICS_RE.sub('\x02\x04\\g<text>\x03', s)
        s = self.HIGHLIGHT_RE.sub('\x02\x04\\g<text>\x03', s)
        s = self.UNDERLINE_RE.sub('\x02\x04\\g<text>\x03', s)
        s = self.STRIKETHROUGH_RE.sub('\x02\x04\\g<text>\x03', s)

        # Find and format headers
        s = self.HEADER_RE1.sub(ansi.with_codes(r'\g<start> \g<name> \g<end>',
                                1), s)
        s = self.HEADER_RE2.sub(ansi.with_codes('\\g<text>\n\\g<underline>',
                                1), s)

        # now return everything to normal, with the ANSI encoding
        s = self.AFTER_RE.sub(self._add_ansi_formatting, s)

        return s
