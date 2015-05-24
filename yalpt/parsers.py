import doctest

class CodeChunk(object):
    def __init__(self, source_obj, source, want=None, exc_msg=None,
                 lineno=None, indent=None):
        self.source = source
        self.want = want
        self.exc_msg = exc_msg
        self.lineno = lineno
        self.indent = indent
        self.source_obj = source_obj
        self.options = {}


class DocTestParser(object):
    def parse(self, literate_string, file_name):
        parser = doctest.DocTestParser()

        for chunk in parser.parse(literate_string, file_name):
            if isinstance(chunk, doctest.Example):
                yield CodeChunk(chunk, chunk.source, chunk.want, chunk.exc_msg,
                                chunk.lineno, chunk.indent)
            else:
                yield chunk
