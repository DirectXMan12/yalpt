import doctest


class CodeChunk(object):
    def __init__(self, source_obj, source, want=None, exc_msg=None,
                 lineno=None, indent=0):
        self.source = source
        self.want = want
        self.exc_msg = exc_msg
        self.lineno = lineno
        self.indent = indent
        self.source_obj = source_obj
        self.options = {}

    def __str__(self):
        return self.source

    def __repr__(self):
        return "<YALPT CodeChunk: %s>" % repr(self.source)


class DocTestParser(object):
    def parse(self, literate_string, file_name):
        parser = doctest.DocTestParser()

        for chunk in parser.parse(literate_string, file_name):
            if isinstance(chunk, doctest.Example):
                yield CodeChunk(chunk, chunk.source, chunk.want, chunk.exc_msg,
                                chunk.lineno, chunk.indent)
            else:
                yield chunk


class MarkdownParser(object):
    def parse(self, literate_string, file_name):
        lines = literate_string.splitlines()
        lines.append(None)

        state = None
        block_start = None
        acc = []
        last_indent = None

        for lineno, line in enumerate(lines):
            first = None
            last_state = state

            if line is None:
                # last line
                state = 'last_line'
            elif state in (None, 'blank_line'):
                if line in ('```', '```python'):
                    state = 'fenced_python'
                    last_indent = 0
                    block_start = lineno + 1
                elif line.startswith('```'):
                    state = 'fenced_other'
                    acc.append(line)
                elif line == '':
                    state = 'blank_line'
                    acc.append(line)
                elif state == 'blank_line' and line.startswith('    '):
                    state = 'indented_python'
                    block_start = lineno
                    first = line[4:]
                else:
                    state = None
                    acc.append(line)
            elif state == 'fenced_python':
                if line == '```':
                    state = None
                elif line != '':
                    # we skip blanks unless dropping down an indentation level
                    # so that the interactive console
                    # doesn't complain
                    indent = len(line) - len(line.lstrip())
                    if indent == 0 and last_indent is not None:
                        if last_indent == 0:
                            state = 'mid_fenced'
                            first = line
                        else:
                            acc.append('')
                            first = line
                            state = 'mid_fenced'
                    else:
                        acc.append(line)

                    last_indent = indent
            elif state == 'fenced_other':
                if line == '```':
                    state = None

                acc.append(line)
            else:
                if line.startswith('    '):
                    state = 'indented_python'
                    acc.append(line[4:])
                elif line == '':
                    state = 'blank_line'
                    first = line
                else:
                    state = None
                    first = line

            if last_state != state:
                if (last_state in ('indented_python', 'fenced_python')
                        or state == 'mid_fenced'):
                    raw_chunk = '\n'.join(acc)+'\n'
                    yield CodeChunk(raw_chunk, raw_chunk, lineno=block_start)
                    if first is not None:
                        acc = [first]
                    else:
                        acc = []

                    if state == 'mid_fenced':
                        state = 'fenced_python'
                        block_start = lineno + 1
                elif state in ('indented_python', 'fenced_python'):
                    yield '\n'.join(acc) + '\n'
                    if first is not None:
                        acc = [first]
                    else:
                        acc = []

                    last_indent = None
                elif state == 'last_line':
                    # it's the last line, and we're in a text block
                    yield '\n'.join(acc)
