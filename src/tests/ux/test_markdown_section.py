# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys

from finance_deep_search.ux.markdown_elements import MarkdownElement, MarkdownSection

from tests.utils import no_linefeeds_text, nonempty_no_linefeeds_text

class TestMarkdownSection(unittest.TestCase):
    """
    Test the MarkdownSection class.
    """
    def assert_section_valid(self,
        section: MarkdownSection, 
        exp_level: int,
        exp_title: str,
        exp_lines: list[MarkdownElement] = [],
        exp_subsections: dict[str,MarkdownSection] = {}):
        self.assertTrue(section.title)
        self.assertEqual(exp_level, section.level, f"<{exp_level}> vs. <{section.level}>")
        self.assertEqual(exp_title, section.title, f"<{exp_title}> vs. <{section.title}>")
        self.assertEqual(exp_lines, section.content, f"<{exp_lines}> vs. <{section.content}>")
        self.assertEqual(exp_subsections, section.subsections, f"<{exp_subsections}> vs. <{section.subsections}>")

    @given(st.integers(min_value=-5, max_value=0))
    def test_make_section_with_nonpositive_level_fails(self, level: int):
        """
        Verify that the level must be > 0.
        """
        with self.assertRaises(AssertionError):
            MarkdownSection(level, 'title')

    @given(st.integers(min_value=1, max_value=4))
    def test_make_section_with_empty_title_fails(self, level: int):
        """
        Verify that if an empty section title is specified an error is raised.
        """
        with self.assertRaises(AssertionError):
            MarkdownSection(level, '')
        with self.assertRaises(AssertionError):
            MarkdownSection(level, None)

    @given(st.integers(min_value=1, max_value=4), nonempty_no_linefeeds_text)
    def test_make_section_with_title_with_no_lines(self, level: int, title: str):
        """
        Verify that a section title is properly formed.
        """
        section = MarkdownSection(level, title)
        self.assert_section_valid(section, level, title)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(st.text()))
    def test_make_section_with_title_with_lines(self, 
        level: int, title: str, lines: list[str]):
        """
        Verify that a section title and initial content of lines are properly formed.
        """
        lines_l = [MarkdownElement(l) for l in lines]
        section = MarkdownSection(level, title, lines)
        self.assert_section_valid(section, level, title, lines_l)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(st.text()),
        st.lists(nonempty_no_linefeeds_text, max_size=5, unique_by = str))
    def test_make_section_with_title_with_lines_and_subsections_as_a_dict(self, 
        level: int, title: str, lines: list[str], subsection_titles: list[str]):
        """
        Verify that a section title, initial content of lines, and initial subsections
        are properly formed.
        """
        lines_l = [MarkdownElement(l) for l in lines]
        subsections_d = dict([(t, MarkdownSection(level+1, t, ['lorem ipsum'])) for t in subsection_titles])
        section = MarkdownSection(level, title, lines, subsections_d)
        self.assert_section_valid(section, level, title, lines_l, subsections_d)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(st.text()),
        st.lists(nonempty_no_linefeeds_text, max_size=5, unique_by = str))
    def test_make_section_with_title_with_lines_and_subsections_as_a_list(self, 
        level: int, title: str, lines: list[str], subsection_titles: list[str]):
        """
        Verify that a section title, initial content of lines, and initial subsections
        are properly formed.
        """
        lines_l = [MarkdownElement(l) for l in lines]
        subsections_l = [MarkdownSection(level+1, t, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        section = MarkdownSection(level, title, lines, subsections_l)
        self.assert_section_valid(section, level, title, lines_l, subsections_d)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(st.text()))
    def test_section_intro_lines_can_be_replaced(self, level: int, title: str, lines: list[str]):
        """
        Verify that add intro lines correctly appends content to a section.
        """
        lines2 = [l+'2' for l in lines]
        lines_l = [MarkdownElement(l) for l in lines]
        lines_l2 = [MarkdownElement(l) for l in lines2]
        section = MarkdownSection(level, title, lines)
        self.assert_section_valid(section, level, title, lines_l)
        section.set_intro_lines(lines2)
        self.assert_section_valid(section, level, title, lines_l2)
        section.set_intro_lines(lines_l2)
        self.assert_section_valid(section, level, title, lines_l2)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(st.text()))
    def test_section_add_intro_lines(self, level: int, title: str, lines: list[str]):
        """
        Verify that add intro lines correctly appends content to a section.
        """
        section = MarkdownSection(level, title)
        self.assert_section_valid(section, level, title)
        lines_l = [MarkdownElement(l) for l in lines]
        section.add_intro_lines(lines) # add list[str]
        self.assert_section_valid(section, level, title, lines_l)
        section.add_intro_lines(lines_l) # add list[MarkdownElement]
        self.assert_section_valid(section, level, title, lines_l+lines_l)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(nonempty_no_linefeeds_text, min_size=1, max_size=5, unique_by = str))
    def test_section_add_subsections(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that add_subsections correctly appends subsections to a section.
        """
        subsections_l = [MarkdownSection(level+1, t, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        section = MarkdownSection(level, title, [], {})
        self.assert_section_valid(section, level, title, [], {})
        section.add_subsections(subsections_l)
        self.assert_section_valid(section, level, title, [], subsections_d)
        new_ss = dict([(ss.title+'2', ss) for ss in subsections_l])
        # print(f"new: {[t[0] for t in new_ss]}, existing keys = {subsections_d.keys()}")
        section.add_subsections(new_ss)
        all_ss = subsections_d.copy()
        all_ss.update(new_ss)
        self.assert_section_valid(section, level, title, [], all_ss)

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(nonempty_no_linefeeds_text, max_size=5, unique_by = str))
    def test_subsections_must_have_new_unique_keys(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that when adding subsections, they all have new, unique keys not already
        in the subsection dictionary.
        """
        subsections_d = dict([(t, MarkdownSection(level+1, t, ['lorem ipsum'])) for t in subsection_titles])
        section = MarkdownSection(level, title, [], subsections_d)
        # Try re-adding each one.
        for key, ss in subsections_d.items():
            with self.assertRaises(ValueError):
                section.add_subsections([ss])
            with self.assertRaises(ValueError):
                section.add_subsections({key:ss})

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text)
    def test_subsections_must_have_levels_greater_than_this_level(self, 
        level: int, title: str):
        """
        Verify that when adding subsections, they all have levels greater than the
        parent section level.
        """
        subsection = MarkdownSection(level, 'Bad')
        with self.assertRaises(ValueError):
            MarkdownSection(level, title, [], [subsection])
        section = MarkdownSection(level, title)
        with self.assertRaises(ValueError):
            section.add_subsections([subsection])

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(nonempty_no_linefeeds_text, min_size=1, max_size=5, unique_by = str))
    def test_section_all_subsections_can_be_replaced(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that add_subsections correctly appends subsections to a section.
        """
        subsections_l = [MarkdownSection(level+1, t, ['lorem ipsum']) for t in subsection_titles]
        subsections_l2 = [MarkdownSection(level+1, t+'2', ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        subsections_d2 = dict([(ss.title, ss) for ss in subsections_l2])
        section = MarkdownSection(level, title, [], subsections_d)
        section.set_subsections(subsections_l2)
        self.assertEqual(len(subsections_l2), len(section.subsections))
        for ss in subsections_l2:
            self.assertEqual(ss, section[ss.title], f"key = {ss.title}")
        section.set_subsections(subsections_d2)
        self.assertEqual(len(subsections_d2), len(section.subsections))
        for key,ss in subsections_d2.items():
            self.assertEqual(ss, section[key], f"key = {key}")

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(nonempty_no_linefeeds_text, min_size=1, max_size=5, unique_by = str))
    def test_section_a_subsection_can_be_replaced_by_index(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that add_subsections correctly appends subsections to a section.
        """
        subsections_l = [MarkdownSection(level+1, t, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        new_ss_d = dict([(t, MarkdownSection(level+1, f'title: {t}')) for t in subsection_titles])
        section = MarkdownSection(level, title, [], subsections_l)
        for key,ss in subsections_d.items():
            section[key] = new_ss_d[key]
            self.assertEqual(new_ss_d[key], section[key], f"key = {key}")

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(st.text()),
        st.lists(nonempty_no_linefeeds_text, max_size=5, unique_by = str))
    def test_section_clear_removes_the_lines_and_subsections(self, 
        level: int, title: str, lines: list[str], subsection_titles: list[str]):
        """
        Verify that `clear` removes the content lines and subsections.
        """
        lines_l = [MarkdownElement(l) for l in lines]
        subsections_l = [MarkdownSection(level+1, t, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        section = MarkdownSection(level, title, lines, subsections_l)
        self.assert_section_valid(section, level, title, lines_l, subsections_d)
        section.clear()
        self.assert_section_valid(section, level, title, [], {})

    @given(st.integers(min_value=1, max_value=4), 
        nonempty_no_linefeeds_text, 
        st.lists(no_linefeeds_text),
        st.lists(nonempty_no_linefeeds_text, max_size=5, unique_by = str))
    def test_section___str__(self, 
        level: int, title: str, lines: list[str], subsection_titles: list[str]):
        """
        Verify that a section string representation is correct.
        """
        lines_l = [MarkdownElement(l) for l in lines]
        subsections_l = [MarkdownSection(level+1, t, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])

        # sanity check: Make SURE we don't have duplicate ss titles and hence fewer dict entries!
        self.assertEqual(len(subsections_l), len(subsections_d)) 
        section = MarkdownSection(level, title, lines_l, subsections_d)
        self.assert_section_valid(section, level, title, lines_l, subsections_d)
        s = str(section)
        all_lines = s.split('\n')
        lines_strs = [str(me) for me in lines_l]
        subsections_strs = [str(ms) for ms in subsections_l]
        exp_lines = f"{'#'*level} {title}\n\n{'\n'.join(lines_strs)}\n{'\n'.join(subsections_strs)}".split('\n')
        self.assertEqual(exp_lines, all_lines, f"exp_lines = <{exp_lines}>, all_lines = <{all_lines}>")

if __name__ == "__main__":
    unittest.main()