# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys

from finance_deep_search.ux.markdown import MarkdownSection

from tests.utils import no_linefeeds_text

class TestMarkdownSection(unittest.TestCase):
    """
    Test the MarkdownSection class.
    """

    def assert_title_level_lines(self,
        section: MarkdownSection, 
        exp_level: int,
        exp_title: str,
        exp_lines: list[str]):
        self.assertEqual(exp_title, section.title, f"<{exp_title}> vs. <{section.title}>")
        self.assertEqual(exp_level, section.level, f"<{exp_level}> vs. <{section.level}>")
        s = str(section)
        all_lines = s.split('\n')
        self.assertTrue(all_lines[0].find('#'*exp_level) >= 0, f"<{all_lines[0]}> contains <{'#'*exp_level}>?")
        self.assertTrue(all_lines[0].find(' '+exp_title) >= 0)
        if len(exp_lines) > 0:
            exp_lines_str = '\n'.join(exp_lines) + '\n'
            self.assertTrue(s.endswith(exp_lines_str), f"<{s}> ?= <{exp_lines_str}>")

    @given(st.integers(min_value=1, max_value=4), no_linefeeds_text)
    def test_section_title_with_no_lines(self, level: int, title: str):
        """
        Verify that a section title line is properly formed.
        """
        section = MarkdownSection(level, title, [])
        self.assert_title_level_lines(section, level, title, [])

    @given(st.integers(min_value=1, max_value=4), no_linefeeds_text, st.lists(st.text()))
    def test_section_title_with_lines(self, level: int, title: str, lines: list[str]):
        """
        Verify that a section title line and body are properly formed.
        """
        section = MarkdownSection(level, title, lines)
        self.assert_title_level_lines(section, level, title, lines)


if __name__ == "__main__":
    unittest.main()