# Common string utilities

def replace_variables(string: str, **variables: dict[str,any]) -> str:
    """
    Replace variables in a string with their values.
    """
    for key, value in variables.items():
        string = string.replace('{{{{'+key+'}}}}', str(value))    
    return string

class MarkdownUtil():
    def __init__(self, 
        default_bullet: str = '*',
        default_indent: str = '\t',
        default_key_format: str = '**%s:**'):
        """
        The `default_key_format` is used to format keys, e.g., `**%s:**` for `key1` will result
        in `**key1:**`. Note the `:` shown; if you want a separator between the key and the value.
        If a method invocation doesn't include the `key_format` argument, then `default_key_format`
        is used. Similarly for `bullet` and `indent` arguments, where `indent` is used for indenting
        hierarchical objects.
        """
        self.default_bullet = default_bullet
        self.default_indent = default_indent
        self.default_key_format = default_key_format

    def __item(self, key: str, item: list[any] | dict[str, any] | str | float | int | tuple,
        bullet: str, indent: str, key_format: str) -> list[str]:

        bullet = self.__value(bullet, self.default_bullet)
        indent = self.__value(indent, self.default_indent)
        key_format = self.__value(key_format, self.default_key_format)

        prefix = f"{bullet} {key_format % (key)}" if key else bullet
        lines = []
        if isinstance(item, list):
            if len(item):
                if key:
                    lines.append(prefix)
                lines2 = self.list_to_markdown(item, bullet, indent, key_format)
                lines.extend([f"{indent}{line}" for line in lines2])
        elif isinstance(item, dict):
            if len(item):
                if key:
                    lines.append(prefix)
                lines2 = self.dict_to_markdown(item, bullet, indent, key_format)
                lines.extend([f"{indent}{line}" for line in lines2])
        else:
            lines.append(f"{prefix} {item}")
        return lines

    def __value(self, s: str, default: str) -> str:
        return s if s else default

    def dict_to_markdown(self, items: dict[str, any], 
        bullet: str = None, indent: str = None, key_format: str = None) -> list[str]:
        lines = []
        for key, value in items.items():
            lines.extend(self.__item(key, value, bullet, indent, key_format))
        return lines

    def list_to_markdown(self, items: list[any], 
        bullet: str = None, indent: str = None, key_format: str = None) -> list[str]:
        """
        The `key_format` value is used for _nested_ dictionaries only. See `MarkdownUtil.__init__`.
        """
        lines = []
        for value in items:
            lines.extend(self.__item(None, value, bullet, indent, key_format))
        return lines

    def to_markdown(self, 
        item: list[any] | dict[str, any] | str | float | int | tuple,
        bullet: str = None, indent: str = None, key_format: str = None) -> list[str]:
        """
        Return hierarchical Markdown bullets as a list for an input `item`.
        For dictionaries, the `key_format` is used to format keys, e.g., `**%s**:`
        applied to `key1` will result in `**key1**:`. Note the `:` shown; if you
        want a separator between the key and the value, add it `key_format`.
        """
        return self.__item(None, item, bullet, indent, key_format)

    def next_indent(self, indent: str) -> str:
        return indent*2 if len(indent) > 0 else '\t'

def try_to_markdown():
    return to_markdown(bullet='*', indent='-', key_decorator='**_', values=[1,2,3], key_values={
        'key1': {
            'key11': 'value11',
            'key12': ['value12a', 'value12b', 'value12c'],
            'key13': {'key13a':'value12a', 'key13b':'value12b', 'key13c':'value12c'},
            'key14': 14,
            'key15': ('15', 'five'),
        },
        'key2': {
            'key21': 'value21',
            'key22': ['value22a', 'value22b', 'value22c'],
            'key23': {'key23a':'value22a', 'key23b':'value22b', 'key23c':'value22c'},
            'key24': 24,
            'key25': ('25', 'five'),
        },
    })

if __name__ == "__main__":
    lines = try_to_markdown()
    print('\n'.join(lines))