from __future__ import annotations
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Callable


class VariableFormat(Enum):
    MARKDOWN = 0
    PLAIN = 1

class Variable():
    def __init__(self,
        key: str, 
        value: any,
        label: str = None, 
        kind: str = 'str'):
        """
        If `label` is `None`, then `make_label(key)` is called to create one.
        If `kind` is `None`, then `format()` will return `None`. Specify
        `None` explicitly for cases where a variable shouldn't be rendered,
        e.g., when verbose output is off.
        """
        self.key = key
        self.value = value
        # Note that we are careful to allow '' for a label.
        self.label = label if label != None else Variable.make_label(key) 
        self.kind = kind

    def __repr__(self) -> str:
        fmt_str = '...' if self.kind else None
        return f"Variable(key = {self.key}, value = {self.value}, label = {self.label}, kind = {fmt_str})"

    @staticmethod
    def get(variable: Variable, default: any) -> any:
        """Return the variables value or default if the variable is None or the value is None."""
        if variable and variable.value:
            return variable.value
        else:
            return default

    def format(self, variable_format: VariableFormat = VariableFormat.PLAIN) -> (str, str, str):
        """
        If `self.kind` is not `None`, then return `(key, label, formatted_value)`.
        Otherwise return `None`. 
        By default, the "plain" format is used, i.e., `str(value)` for most values. 
        Pass `variable_format = VariableFormat.MARKDOWN` for markdown formatting, e.g.,
        a 'url' is returned `[key](value)`, for 'file' it is `[value](file://value)`. 
        """
        if not self.kind:
            return None
        
        formatter_map = None
        match variable_format:
            case VariableFormat.PLAIN:
                formatter_map = Variable.plain_formats
            case VariableFormat.MARKDOWN:
                formatter_map = Variable.markdown_formats
            case _:
                raise ValueError(f"Invalid variable_format value: {variable_format}")
        
        formatter = formatter_map.get(self.kind)
        if not formatter:
            raise ValueError(f"Unrecognized kind specified: {self.kind}")

        return (self.key, self.label, formatter(self))

    # Class utilities:

    def make_label(s: str) -> str:
        """Replace '_' with ' ', capitalize words and strip whitespace on the ends."""
        return s.replace('_', ' ').title().strip()

    def make_formatted(variables: Sequence[Variable], variable_format: VariableFormat = VariableFormat.PLAIN) -> list[(str,str,str)]:
        """
        A helper method for common uses of Variables; return a list of
        `(key, label, formatted(value))` pairs from the input sequence of
        Variables, filtering out any were `variable.format() == `None`.
        The `variable_format` argument is passed to `format()`.
        """
        result = []
        for variable in variables:
            tuple = variable.format(variable_format=variable_format)
            if tuple:
                result.append(tuple)
        return result

    provider_names = {
        'openai':    'OpenAI',
        'anthropic': 'Anthropic',
        'ollama':    'Ollama',
    }

    def get_value(variable: Variable, default: any = None) -> any | None:
        if variable:
            return variable.value if variable.value else default
        else:
            return default
    
    markdown_formats: dict[str, Callable[[Variable],str]] = {
        'str':            lambda v: str(v.value),
        'url':            lambda v: f"[{v.label}]({v.value})" if v.value else "None",
        'file':           lambda v: f"[`{v.value}`](file://{v.value})" if v.value else "None",
        'code':           lambda v: f"`{v.value}`",
        'code_multiline': lambda v: f"```\n{v.value}\n```",
        'dict':           lambda v: '\n'.join([f"`{key}`: {value}" for key,value in v.value.items()]) if v.value else "None",
        'callout':        lambda v: '\n'.join([f"> {line}" for line in str(v.value).split('\n')]) if v.value else "None",
        'provider':       lambda v: Variable.provider_names.get(v.value),
    }
    plain_formats: dict[str, Callable[[Variable],str]] = {
        'str':            lambda v: str(v.value),
        'url':            lambda v: str(v.value),
        'file':           lambda v: str(v.value),
        'code':           lambda v: str(v.value),
        'code_multiline': lambda v: str(v.value),
        'dict':           lambda v: '\n'.join([f"{key}: {value}" for key,value in v.value.items()]) if v.value else "None",
        'callout':        lambda v: str(v.value),
        'provider':       lambda v: Variable.provider_names.get(v.value),
    }

