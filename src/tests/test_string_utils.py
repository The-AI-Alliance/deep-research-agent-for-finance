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

from finance_deep_search.string_utils import replace_variables

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

if __name__ == "__main__":
    unittest.main()