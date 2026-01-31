# Unit tests for the "path utils" module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os

from tests.utils import nonempty_no_slash_text, parent_path_text

from common.path_utils import resolve_path

class TestPathUtils(unittest.TestCase):
    """
    Test the path- and file-related utilities.
    """

    @given(parent_path_text, nonempty_no_slash_text)
    def test_resolve_path(self, parents: str, file: str):
        actual = resolve_path(file, parents)
        expected = Path(os.path.join(parents, file)
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()