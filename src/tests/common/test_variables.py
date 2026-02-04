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

from common.variables import Variable

class TestVariables(unittest.TestCase):
    """
    Test variables utility.
    """
    save_ux = Variable.which_ux

    @classmethod
    def setUpClass(cls):
        TestVariables.save_ux = Variable.which_ux
        Variable.set_ux('markdown')

    @classmethod
    def tearDownClass(cls):
        # Restore to where it was
        Variable.set_ux(TestVariables.save_ux)

    @given(
        st.dictionaries(no_brace_nonempty_text(), no_brace_text()), 
        parent_path_text(),         # URL parent path
        no_brace_nonempty_text(),  # URL end
        parent_path_text(),         # file name parent path
        no_brace_nonempty_text(),  # file name end
        no_brace_nonempty_text(),  # code
        st.sampled_from(['openai', 'anthropic', 'ollama']),
        st.sampled_from(['rich', 'markdown']))
    def test_Variable_construction(self, 
        kvs: dict[str, str], 
        url_parent, url_end,
        file_parent, file_end,
        code, provider, ux):

        d = {'one': 1, 'two': 2.2, 'really': True}
        d_str = '\n'.join([f"`{k}`: {v}" for k,v in d.items()])
        variables = [Variable(k,v) for k,v in kvs.items()]
        variables.extend([
            Variable('url_formatter',      f"https://{url_parent}/{url_end}", formatter=Variable.url_formatter),
            Variable('file_url_formatter', f"{file_parent}/{file_end}", formatter=Variable.file_url_formatter),
            Variable('code_formatter',     code, formatter=Variable.code_formatter),
            Variable('dict_formatter',     d, formatter=Variable.dict_formatter),
            Variable('provider_names',     provider, formatter=Variable.provider_names),
            Variable('ux_names',           ux, formatter=Variable.ux_names),
        ])
        expected_fmts = [str for v in kvs.values()]
        expected_fmts.extend([
            Variable.url_formatter,
            Variable.file_url_formatter,
            Variable.code_formatter,
            Variable.dict_formatter,
            Variable.provider_names,
            Variable.ux_names,
        ])
        expected_strs = [str(v) for v in kvs.values()]
        expected_strs.extend([
            f"[https://{url_parent}/{url_end}](https://{url_parent}/{url_end})",
            f"[`{file_parent}/{file_end}`](file://{file_parent}/{file_end})",
            f"`{code}`",
            d_str,
            Variable.provider_names.get(provider),
            Variable.ux_names.get(ux),
        ])

        keys = list(kvs.keys())
        for i in range(len(keys)):
            variable = variables[i]
            key, label, value_str = variable.format()
            self.assertEqual(variable.key, key)
            self.assertEqual(keys[i], key)
            self.assertEqual(Variable.make_label(keys[i]), label)
        for i in range(len(variables)):
            variable = variables[i]
            key, label, value_str = variable.format()
            self.assertEqual(variable.key, key)
            self.assertEqual(variable.label, label)
            self.assertEqual(Variable.make_label(key), label)
            self.assertEqual(expected_fmts[i], variable.formatter)
            self.assertEqual(expected_strs[i], value_str)

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

    @given(no_brace_text())
    def test_Variable_format_returns_None_if_formatter_None(self, string: str):
        variable = Variable(string, string + "_value", formatter=None)
        self.assertEqual(None, variable.format())

    @given(no_brace_text())
    def test_Variable_format_returns_simple_str_if_use_basic_formatting_true(self, string: str):
        vstr = string + "_value"
        variable = Variable(string, vstr, formatter=str)
        _, _, actual = variable.format(use_basic_formatting=True)
        self.assertEqual(vstr, actual)

    @given(st.sampled_from(['rich', 'markdown']))
    def test_Variable_ux_names(self, ux):
        variable1 = Variable('ux', ux, formatter=Variable.ux_names)
        _, _, str1 = variable1.format()
        self.assertEqual(Variable.ux_names[ux], str1)
        # Unknown ux value? format() returns the variable's key.
        variable2 = Variable('ux', 'bad', formatter=Variable.ux_names)
        _, _, str2 = variable2.format()
        self.assertEqual(variable2.key, str2)

    @given(st.sampled_from(['openai', 'anthropic', 'ollama']))
    def test_Variable_provider_names(self, provider):
        variable1 = Variable('provider', provider, formatter=Variable.provider_names)
        _, _, str1 = variable1.format()
        self.assertEqual(Variable.provider_names[provider], str1)
        # Unknown provider value? format() returns the variable's key.
        variable2 = Variable('provider', 'bad', formatter=Variable.provider_names)
        _, _, str2 = variable2.format()
        self.assertEqual(variable2.key, str2)

if __name__ == "__main__":
    unittest.main()