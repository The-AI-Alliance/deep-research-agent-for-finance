# Unit tests for the "string utils" module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys

from tests.utils import (
    nonempty_text,
    no_brace_text,
    no_brace_non_empty_text,
)

from finance_deep_search.string_utils import replace_variables, MarkdownUtil

class TestStringUtils(unittest.TestCase):
    """
    Test the string-related utilities.
    """

    @given(st.dictionaries(no_brace_non_empty_text, no_brace_text), st.text(), st.text())
    def test_replace_variables_replaces_keys_with_values(self, 
        kvs: dict[str, str], delimiter, prefix_suffix):
        """
        Verify that the keys are are properly replaced with the corresponding values
        in the text.
        We ignore whitespace at the beginnings and the ends of strings.
        """
        key_strs = ['{{{{'+str(key)+'}}}}' for key in kvs.keys()]
        text = f'{prefix_suffix}{delimiter.join(key_strs)}{prefix_suffix}'
        expected_text = f'{prefix_suffix}{delimiter.join(kvs.values())}{prefix_suffix}'
        actual_text = replace_variables(text, **kvs)
        et = expected_text.strip()
        at = actual_text.strip()
        self.assertEqual(et, at,
            f'<{et}> != <{at}> (kvs: {kvs}, text = {text})')

    @given(
        st.dictionaries(no_brace_non_empty_text, no_brace_text),
        st.dictionaries(no_brace_non_empty_text, no_brace_text),
        st.integers(),
        st.floats(),
        st.tuples(st.text(), st.text()),
        st.sampled_from(['*', '-']),
        st.sampled_from(['  ', '--']),
        st.sampled_from(["%s", '**%s:%%', '_%s_', '**_%s:_**']))
    def test_MarkdownUtil_returns_markdown(self, 
        kvs1: dict[str, any], kvs2: dict[str, any], 
        int_val: int, float_val: float, tuple_val: tuple[str, str],
        bullet: str, indent: str, key_format: str):
        """
        Verify that the dictionaries are correctly converted to nested markdown lists.
        """
        # Arbitrarily replace the len(kvs1)/2 element with kvs2.
        index = -1
        kvs = kvs1
        if len(kvs) > 0:
            kvs2.update({'int': int_val})
            kvs2.update({'float': float_val})
            kvs2.update({'tuple': tuple_val})
            kvs2.update({'list': [int_val, float_val, tuple_val]})
            index = int(len(kvs)/2)
            kvs.update({list(kvs)[index]: kvs2})

        expected = []
        for key, value in kvs1.items():
            prefix = f"{indent}{bullet} {key_format}" % (key)
            if isinstance(value, dict):
                indent2 = indent*2 if len(indent) > 0 else '  '
                expected.append(prefix)
                for k, v in kvs2.items():
                    prefix2 = f"{indent2}{bullet} {key_format}" % (k)
                    if isinstance(v, list):
                        expected.append(f"{prefix2}")
                        expected.extend([f"{indent}{indent2}{bullet} {v2}" for v2 in v])
                    else:
                        expected.append(f"{prefix2} {v}")
            else:
                expected.append(f"{prefix} {value}")
        mu = MarkdownUtil()
        actual = mu.to_markdown(kvs1, bullet, indent, key_format)
        expected_str = '\n'.join(expected)
        self.assertEqual(expected, actual, f"<\n{'\n'.join(expected)}\n> != <\n{'\n'.join(actual)}\n>, kvs = <{kvs}>")

if __name__ == "__main__":
    unittest.main()