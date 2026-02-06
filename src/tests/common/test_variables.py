# Unit tests for the "variables" module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys

from tests.utils import (
    no_brace_text,
    no_brace_nonempty_text,
    parent_path_text,
)

from common.string_utils import to_id
from common.variables import Variable, VariableFormat

class TestVariables(unittest.TestCase):
    """
    Test variables utility.
    """
    provider_map = {'openai': 'OpenAI', 'anthropic': 'Anthropic', 'ollama': 'Ollama'}
    
    def check_all(self,
        kvs: dict[str, str], 
        url_parent, url_end,
        file_parent, file_end,
        code, provider, format):

        d = {'one': 1, 'two': 2.2, 'really': True}
        d_str = '\n'.join([f"`{k}`: {v}" for k,v in d.items()])
        variables = [Variable(k,v) for k,v in kvs.items()]
        variables.extend([
            Variable('url',             f"https://{url_parent}/{url_end}", kind='url'),
            Variable('file',            f"{file_parent}/{file_end}", kind='file'),
            Variable('code',            code, kind='code'),
            Variable('code_multiline',  code, kind='code_multiline'),
            Variable('dict',            d, kind='dict'),
            Variable('provider',        provider, kind='provider'),
        ])
        expected_fmts = ['str' for v in kvs.values()]
        expected_fmts.extend([
            'url',
            'file',
            'code',
            'code_multiline',
            'dict',
            'provider',
        ])
        expected_strs = [str(v) for k,v in kvs.items()]
        if format == VariableFormat.MARKDOWN:
            expected_strs.extend([
                f"[Url](https://{url_parent}/{url_end})",
                f"[`{file_parent}/{file_end}`](file://{file_parent}/{file_end})",
                f"`{code}`",
                f"```\n{code}\n```",
                '\n'.join([f"`{k}`: {v}" for k,v in d.items()]),
                TestVariables.provider_map.get(provider),
            ])
        else:
            expected_strs.extend([
                f"https://{url_parent}/{url_end}",
                f"{file_parent}/{file_end}",
                code,
                code,
                '\n'.join([f"{k}: {v}" for k,v in d.items()]),
                TestVariables.provider_map.get(provider),
            ])

        keys = list(kvs.keys())
        for i in range(len(keys)):
            variable = variables[i]
            key, label, value_str = variable.format(variable_format=format)
            self.assertEqual(variable.key, key)
            self.assertEqual(keys[i], key)
            self.assertEqual(Variable.make_label(keys[i]), label)
        for i in range(len(variables)):
            variable = variables[i]
            key, label, value_str = variable.format(variable_format=format)
            self.assertEqual(variable.key, key)
            self.assertEqual(variable.label, label)
            self.assertEqual(Variable.make_label(key), label)
            self.assertEqual(expected_fmts[i], variable.kind)
            self.assertEqual(expected_strs[i], value_str, f"{i}, {format}")

    @given(
        st.dictionaries(no_brace_nonempty_text(), no_brace_text()), 
        parent_path_text(),        # URL parent path
        no_brace_nonempty_text(),  # URL end
        parent_path_text(),        # file name parent path
        no_brace_nonempty_text(),  # file name end
        no_brace_nonempty_text(),  # code
        st.sampled_from(['openai', 'anthropic', 'ollama']),
        st.sampled_from([VariableFormat.MARKDOWN, VariableFormat.PLAIN]))
    def test_Variable_construction(self, 
        kvs: dict[str, str], 
        url_parent, url_end,
        file_parent, file_end,
        code, provider, format):

        self.check_all(kvs, url_parent, url_end, file_parent, file_end, code, provider, format)

    @given(
        st.dictionaries(no_brace_nonempty_text(), no_brace_text()), 
        parent_path_text(),        # URL parent path
        no_brace_nonempty_text(),  # URL end
        parent_path_text(),        # file name parent path
        no_brace_nonempty_text(),  # file name end
        no_brace_nonempty_text(),  # code
        st.sampled_from(['openai', 'anthropic', 'ollama']))
    def test_markdown_formatting(self, 
        kvs: dict[str, str], 
        url_parent, url_end,
        file_parent, file_end,
        code, provider):

        self.check_all(kvs, url_parent, url_end, file_parent, file_end, code, provider, VariableFormat.MARKDOWN)

    @given(
        st.dictionaries(no_brace_nonempty_text(), no_brace_text()), 
        parent_path_text(),        # URL parent path
        no_brace_nonempty_text(),  # URL end
        parent_path_text(),        # file name parent path
        no_brace_nonempty_text(),  # file name end
        no_brace_nonempty_text(),  # code
        st.sampled_from(['openai', 'anthropic', 'ollama']))
    def test_plain_formatting(self, 
        kvs: dict[str, str], 
        url_parent, url_end,
        file_parent, file_end,
        code, provider):

        self.check_all(kvs, url_parent, url_end, file_parent, file_end, code, provider, VariableFormat.PLAIN)

    @given(no_brace_text())
    def test_Variable_label_created_if_not_provided(self, string: str):
        # Add leading letter...''
        s = 'a'+string
        expected=s.replace('_', ' ').title().strip()
        variable = Variable(s, expected)
        self.assertEqual(expected, variable.label)
        self.assertTrue(variable.label != variable.key)

    @given(no_brace_text())
    def test_Variable_make_label(self, string: str):
        expected=string.replace('_', ' ').title().strip()
        self.assertEqual(expected, Variable.make_label(string))

    @given(no_brace_nonempty_text())
    def test_Variable_get_returns_default_if_variable_or_value_None(self, string: str):
        v = Variable('key', None)
        self.assertEqual(str, Variable.get(v, str))
        self.assertEqual(str, Variable.get(None, str))

    @given(no_brace_nonempty_text())
    def test_Variable_get_returns_value_if_variable_and_value_not_None(self, string: str):
        v = Variable('key', str)
        self.assertEqual(str, Variable.get(v, None))

    @given(no_brace_text())
    def test_Variable_format_returns_None_if_format_None(self, string: str):
        variable = Variable(string, string + "_value", kind=None)
        self.assertEqual(None, variable.format())

    @given(no_brace_text())
    def test_Variable_format_returns_simple_str_if_use_plain_formatting(self, string: str):
        vstr = string + "_value"
        variable = Variable(string, vstr)
        _, _, actual = variable.format(variable_format=VariableFormat.PLAIN)
        self.assertEqual(vstr, actual)

    @given(no_brace_text())
    def test_Variable_format_returns_formatted_str_if_format_not_None(self, string: str):
        vstr = string + "_value"
        variable = Variable(string, vstr, kind='str')
        _, _, actual = variable.format()
        self.assertEqual(vstr, actual)

    def test_Variable_format_returns_None_str_if_value_None(self):
        for s in ['str', 'url', 'file', 'dict', 'callout']:
            variable = Variable(s, None, kind=s)
            self.assertEqual((s, Variable.make_label(s), 'None'), variable.format())

    def test_Variable_get_value_returns_default_if_variable_arg_None_or_value_None(self):
        s = 'key'
        # default is None:
        self.assertEqual(None, Variable.get_value(None))
        self.assertEqual(None, Variable.get_value(Variable(s, None)))
        self.assertEqual("Not None", Variable.get_value(Variable(s, "Not None")))
        # default is something else...
        self.assertEqual("hello", Variable.get_value(None, default="hello"))
        self.assertEqual("hello", Variable.get_value(Variable(s, None), default="hello"))
        self.assertEqual("Not None", Variable.get_value(Variable(s, "Not None"), default="hello"))

    @given(no_brace_nonempty_text(max_size=16), no_brace_nonempty_text(max_size=16))
    def test_Variable___repr__(self, label: str, value: str):
        key = to_id(label)
        v1 = Variable(key, value, label=label, kind='code')
        actual = str(v1)
        expected = f"Variable(key = {key}, value = {value}, label = {label}, kind = ...)"
        self.assertEqual(expected, actual)
        v2 = Variable(key, value, label=label, kind=None)
        actual = str(v2)
        expected = f"Variable(key = {key}, value = {value}, label = {label}, kind = None)"
        self.assertEqual(expected, actual)

    @given(st.sampled_from(['openai', 'anthropic', 'ollama']))
    def test_provider_with_valid_value(self, provider):
        variable = Variable('provider', provider, kind='provider')
        _, _, str = variable.format()
        self.assertEqual(TestVariables.provider_map[provider], str)


    @given(st.sampled_from(['openai', 'anthropic', 'ollama']))
    def test_provider_with_invalid_value(self, provider):
        variable = Variable('provider', 'bad', kind='provider')
        _, _, str = variable.format()
        self.assertEqual(None, str)

if __name__ == "__main__":
    unittest.main()