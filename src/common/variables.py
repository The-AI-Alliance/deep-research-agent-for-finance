from __future__ import annotations
from collections.abc import Sequence
from pathlib import Path
from typing import Callable

class Variable():
    def __init__(self,
        key: str, 
        value: any,
        label: str = None, 
        formatter: Callable[[any],str] | dict | None = str):
        """
        If `label` is `None`, then `make_label(key)` is called to create one.
        If `formatter` is `None`, then `format()` will return `None`. Specify
        `None` explicitly for cases where a variable shouldn't be rendered,
        e.g., when verbose output is off.
        """
        self.key = key
        self.value = value
        # Note that we are careful to allow '' for a label.
        self.label = label if label != None else Variable.make_label(key) 
        self.formatter = formatter

    def __repr__(self) -> str:
        fmt_str = '...' if self.formatter else None
        return f"Variable(key = {self.key}, value = {self.value}, label = {self.label}, formatter = {fmt_str})"

    @staticmethod
    def get(variable: Variable, default: any) -> any:
        """Return the variables value or default if the variable is None or the value is None."""
        if variable and variable.value:
            return variable.value
        else:
            return default

    def format(self, use_basic_formatting: bool = False) -> (str, str, str):
        """
        If formatter is not `None`, then return `(key, label, formatter(value))`.
        Otherwise return `None`. 
        Pass `use_basic_formatting = True` to just print values with `str(value)`,
        such as when writing to the console on startup, before the display UX is 
        initialized, for example. Just as for normal formatting, whether or not to
        print a variable in this case is still decided by whether or not formatter is None.
        """
        if not self.formatter:
            return None
        if use_basic_formatting:
            return (self.key, self.label, str(self.value))
        elif isinstance(self.formatter, dict):
            return (self.key, self.label, self.formatter.get(self.value, str(self.key)))
        else:
            return (self.key, self.label, self.formatter(self.value))

    # Class utilities:

    def make_label(s: str) -> str:
        """Replace '_' with ' ', capitalize words and strip whitespace on the ends."""
        return s.replace('_', ' ').title().strip()

    def make_formatted(variables: Sequence[Variable], use_basic_formatting: bool = False) -> list[(str,str)]:
        """
        A helper method for common uses of Variables; return a list of
        `(label, formatted(value))` pairs from the input sequence of
        Variables, filtering out any were `variable.format() == `None`.
        The `use_basic_formatting` argument is passed to `format()`.
        """
        result = []
        for variable in variables:
            tuple = variable.format(use_basic_formatting=use_basic_formatting)
            if tuple:
                result.append((tuple[1], tuple[2]))
        return result

    which_ux: str = 'rich'

    provider_names = {
        'openai':    'OpenAI',
        'anthropic': 'Anthropic',
        'ollama':    'Ollama',
    }

    # Keep consistent with set_ux() below!
    ux_names = {
        'rich':      'Rich',
        'markdown':  'Markdown',
    }
    
    url_formatter_md              = lambda u: f"[{u}]({u})"
    file_url_formatter_md         = lambda f: f"[`{f}`](file://{f})"
    code_formatter_md             = lambda s: f"`{s}`"
    code_formatter_multiline_md   = lambda s: f"```\n{s}\n```"
    dict_formatter_md             = lambda d: '\n'.join([f"`{k}`: {v}" for k,v in d.items()])
    callout_formatter_md          = lambda s: '\n'.join([f"> {line}" for line in str(s).split('\n')])

    url_formatter_rich            = lambda u: str(u)
    file_url_formatter_rich       = lambda f: str(f)
    code_formatter_rich           = lambda s: str(s)
    code_formatter_multiline_rich = lambda s: str(s)
    dict_formatter_rich           = lambda d: '\n'.join([f"{k}: {v}" for k,v in d.items()])
    callout_formatter_rich        = lambda s: str(s)

    url_formatter                 = url_formatter_rich
    file_url_formatter            = file_url_formatter_rich
    code_formatter                = code_formatter_rich
    code_formatter_multiline      = code_formatter_multiline_rich
    dict_formatter                = dict_formatter_rich
    callout_formatter            = callout_formatter_rich

    # Keep consistent with ux_names above!
    def set_ux(ux: str):
        """
        Specifying the UX allows proper formatting to be returned for
        URLs, files, code etc.
        """
        Variable.which_ux = ux
        match ux:
            case 'rich':
                Variable.url_formatter            = Variable.url_formatter_rich
                Variable.file_url_formatter       = Variable.file_url_formatter_rich
                Variable.code_formatter           = Variable.code_formatter_rich
                Variable.code_formatter_multiline = Variable.code_formatter_multiline_rich
                Variable.dict_formatter           = Variable.dict_formatter_rich
                Variable.callout_formatter        = Variable.callout_formatter_rich
            case 'markdown':
                Variable.url_formatter            = Variable.url_formatter_md
                Variable.file_url_formatter       = Variable.file_url_formatter_md
                Variable.code_formatter           = Variable.code_formatter_md
                Variable.code_formatter_multiline = Variable.code_formatter_multiline_md
                Variable.dict_formatter           = Variable.dict_formatter_md
                Variable.callout_formatter        = Variable.callout_formatter_md
            case _:
                raise ValueError(f"Unrecognized 'ux' value: {ux}")

