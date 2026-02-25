# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys

from dra.core.common.markdown.elements import MarkdownElement, MarkdownSection

from dra.core.common.utils.strings import to_id

from tests.dra.utils import no_linefeeds_text, no_linefeeds_nonempty_text

class TestMarkdownSection(unittest.TestCase):
    """
    Test the MarkdownSection class.
    """
    def assert_section_valid(self,
        section: MarkdownSection, 
        exp_title: str,
        exp_level: int,
        exp_content: list[MarkdownElement] = [],
        exp_subsections: dict[str,MarkdownSection] = {}):
        self.assertTrue(section.title)
        self.assertEqual(exp_level, section.level, f"<{exp_level}> vs. <{section.level}>")
        self.assertEqual(exp_title, section.title, f"<{exp_title}> vs. <{section.title}>")
        self.assertEqual(exp_content, section.content, f"<{exp_content}> vs. <{section.content}>")
        self.assertEqual(exp_subsections, section.subsections, f"<{exp_subsections}> vs. <{section.subsections}>")

    @given(st.integers(min_value=-5, max_value=0))
    def test_make_section_with_nonpositive_level_fails(self, level: int):
        """
        Verify that the level must be > 0.
        """
        with self.assertRaises(AssertionError):
            MarkdownSection('title', level)

    @given(st.integers(min_value=1, max_value=4))
    def test_make_section_with_empty_title_fails(self, level: int):
        """
        Verify that an empty section title raises an error.
        """
        with self.assertRaises(AssertionError):
            MarkdownSection('', level)
        with self.assertRaises(AssertionError):
            MarkdownSection(None, level)

    @given(no_linefeeds_nonempty_text())
    def test_make_section_with_title_has_level_1_and_no_content_nor_subsections(self, title: str):
        """
        Verify that a section with just a title has level == 1 
        and empty content and subsections.
        """
        section = MarkdownSection(title)
        self.assert_section_valid(section, title, 1)

    @given(st.integers(min_value=1, max_value=4), no_linefeeds_nonempty_text())
    def test_make_section_with_title_with_no_content(self, level: int, title: str):
        """
        Verify that a section with just a level and title is properly formed.
        """
        section = MarkdownSection(title, level)
        self.assert_section_valid(section, title, level)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(st.text()))
    def test_make_section_with_title_with_content(self, 
        level: int, title: str, content: list[str]):
        """
        Verify that a section with level, title, and initial content is properly formed.
        """
        content_l = [MarkdownElement(l) for l in content]
        section = MarkdownSection(title, level, content)
        self.assert_section_valid(section, title, level, content_l)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(st.text()),
        st.lists(no_linefeeds_nonempty_text(), max_size=5, unique_by = str))
    def test_make_section_with_title_with_content_and_subsections_as_a_dict(self, 
        level: int, title: str, content: list[str], subsection_titles: list[str]):
        """
        Verify that a section with level, title, initial content, and initial 
        subsections dict is properly formed.
        """
        content_l = [MarkdownElement(l) for l in content]
        subsections_d = dict([(t, MarkdownSection(t, level+1, ['lorem ipsum'])) for t in subsection_titles])
        section = MarkdownSection(title, level, content, subsections_d)
        self.assert_section_valid(section, title, level, content_l, subsections_d)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(st.text()),
        st.lists(no_linefeeds_nonempty_text(), max_size=5, unique_by = str))
    def test_make_section_with_title_with_content_and_subsections_as_a_list(self, 
        level: int, title: str, content: list[str], subsection_titles: list[str]):
        """
        Verify that a section with level, title, initial content, and initial 
        subsections list is properly formed.
        """
        content_l = [MarkdownElement(l) for l in content]
        subsections_l = [MarkdownSection(t, level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        section = MarkdownSection(title, level, content, subsections_l)
        self.assert_section_valid(section, title, level, content_l, subsections_d)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(st.text()))
    def test_section_intro_content_can_be_replaced(self,
        level: int, title: str, content: list[str]):
        """
        Verify that `set_intro_content` correctly replaces the content in a section.
        """
        content2 = [l+'2' for l in content]
        content_l = [MarkdownElement(l) for l in content]
        content_l2 = [MarkdownElement(l) for l in content2]
        section = MarkdownSection(title, level, content)
        self.assert_section_valid(section, title, level, content_l)
        section.set_intro_content(content2)
        self.assert_section_valid(section, title, level, content_l2)
        section.set_intro_content(content_l2)
        self.assert_section_valid(section, title, level, content_l2)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(st.text()))
    def test_section_add_intro_content_adds_to_the_existing_content(self,
        level: int, title: str, content: list[str]):
        """
        Verify that `add_intro_content` correctly appends content to a section.
        """
        section = MarkdownSection(title, level)
        self.assert_section_valid(section, title, level)
        content_l = [MarkdownElement(l) for l in content]
        section.add_intro_content(content) # add list[str]
        self.assert_section_valid(section, title, level, content_l)
        section.add_intro_content(content_l) # add list[MarkdownElement]
        self.assert_section_valid(section, title, level, content_l+content_l)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        no_linefeeds_nonempty_text())
    def test_section_add_intro_content_rejects_MarkdownSections(self,
        level: int, title: str, title2: str):
        """
        Verify that attempting to add a MarkdownSection using `add_intro_content` fails.
        """
        section = MarkdownSection(title, level)
        self.assert_section_valid(section, title, level)
        section2 = MarkdownSection(title2, level+1)
        with self.assertRaises(ValueError):
            section.add_intro_content([section2])

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(no_linefeeds_nonempty_text(), min_size=1, max_size=5, unique_by = str))
    def test_section_add_subsections_adds_to_the_existing_subsections(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that add_subsections correctly appends subsections to a section.
        """
        subsections_l = [MarkdownSection(t, level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        section = MarkdownSection(title, level, [], {})
        self.assert_section_valid(section, title, level, [], {})
        section.add_subsections(subsections_l)
        self.assert_section_valid(section, title, level, [], subsections_d)
        new_ss = dict([(ss.title+'2', ss) for ss in subsections_l])
        # print(f"new: {[t[0] for t in new_ss]}, existing keys = {subsections_d.keys()}")
        section.add_subsections(new_ss)
        all_ss = subsections_d.copy()
        all_ss.update(new_ss)
        self.assert_section_valid(section, title, level, [], all_ss)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(no_linefeeds_nonempty_text(), max_size=5, unique_by = str))
    def test_subsections_must_have_new_unique_keys(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that when adding subsections, they all have new, unique keys not already
        in the subsection dictionary.
        """
        subsections_d = dict([(t, MarkdownSection(t, level+1, ['lorem ipsum'])) for t in subsection_titles])
        section = MarkdownSection(title, level, [], subsections_d)
        # Try re-adding each one.
        for key, ss in subsections_d.items():
            with self.assertRaises(ValueError):
                section.add_subsections([ss])
            with self.assertRaises(ValueError):
                section.add_subsections({key:ss})

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text())
    def test_subsections_must_be_of_type_MarkdownSection(self, 
        level: int, title: str):
        """
        Verify that when adding subsections, all of them must be MarkdownSections.
        """
        elem = MarkdownElement('Bad')
        with self.assertRaises(ValueError):
            MarkdownSection(title, level, [], [elem])
        section = MarkdownSection(title, level)
        with self.assertRaises(ValueError):
            section.add_subsections([elem])

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text())
    def test_subsections_levels_will_be_reset_to_be_one_larger_if_not_already_larger(self, 
        level: int, title: str):
        """
        Verify that when adding subsections, their levels will be changed to
        parent.level+1 is not >= parent.level+1.
        """
        subsection1   = MarkdownSection('Bad1',   1)
        subsection11  = MarkdownSection('Bad11',  1)
        subsection12  = MarkdownSection('Bad12',  1)
        subsection2   = MarkdownSection('Bad2',   1)
        subsection21  = MarkdownSection('Bad21',  1)
        subsection22  = MarkdownSection('Bad22',  1)
        subsection221 = MarkdownSection('Bad221', 1)
        section = MarkdownSection(title, 2)
        subsection1.add_subsections([subsection11, subsection12])
        subsection22.add_subsections([subsection221])
        subsection2.add_subsections([subsection21, subsection22])
        section.add_subsections([subsection1, subsection2])

        self.assertEqual(3, subsection1.level)
        self.assertEqual(3, subsection2.level)
        self.assertEqual(4, subsection11.level)
        self.assertEqual(4, subsection12.level)
        self.assertEqual(4, subsection21.level)
        self.assertEqual(4, subsection22.level)
        self.assertEqual(5, subsection221.level)

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(no_linefeeds_nonempty_text(), min_size=1, max_size=5, unique_by = str))
    def test_section_all_subsections_can_be_replaced(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that add_subsections correctly appends subsections to a section.
        """
        subsections_l = [MarkdownSection(t, level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_l2 = [MarkdownSection(t+'2', level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        subsections_d2 = dict([(ss.title, ss) for ss in subsections_l2])
        section = MarkdownSection(title, level, [], subsections_d)
        section.set_subsections(subsections_l2)
        self.assertEqual(len(subsections_l2), len(section.subsections))
        for ss in subsections_l2:
            self.assertEqual(ss, section[ss.title], f"key = {ss.title}")
        section.set_subsections(subsections_d2)
        self.assertEqual(len(subsections_d2), len(section.subsections))
        for key,ss in subsections_d2.items():
            self.assertEqual(ss, section[key], f"key = {key}")

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(no_linefeeds_nonempty_text(), min_size=1, max_size=5, unique_by = str))
    def test_section_a_subsection_can_be_replaced_by_index(self, 
        level: int, title: str, subsection_titles: list[str]):
        """
        Verify that add_subsections correctly appends subsections to a section.
        """
        subsections_l = [MarkdownSection(t, level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        new_ss_d = dict([(t, MarkdownSection(f'title: {t}', level+1)) for t in subsection_titles])
        section = MarkdownSection(title, level, [], subsections_l)
        for key,ss in subsections_d.items():
            section[key] = new_ss_d[key]
            self.assertEqual(new_ss_d[key], section[key], f"key = {key}")

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(st.text()),
        st.lists(no_linefeeds_nonempty_text(), max_size=5, unique_by = str))
    def test_section_clear_removes_the_content_and_subsections(self, 
        level: int, title: str, content: list[str], subsection_titles: list[str]):
        """
        Verify that `clear` removes the content content and subsections.
        """
        content_l = [MarkdownElement(l) for l in content]
        subsections_l = [MarkdownSection(t, level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])
        section = MarkdownSection(title, level, content, subsections_l)
        self.assert_section_valid(section, title, level, content_l, subsections_d)
        section.clear()
        self.assert_section_valid(section, title, level, [], {})

    @given(st.integers(min_value=1, max_value=4), 
        no_linefeeds_nonempty_text(), 
        st.lists(no_linefeeds_text()),
        st.lists(no_linefeeds_nonempty_text(), max_size=5, unique_by = str))
    def test_section___repr__(self, 
        level: int, title: str, content: list[str], subsection_titles: list[str]):
        """
        Verify that a section string representation is correct.
        """
        content_l = [MarkdownElement(l) for l in content]
        subsections_l = [MarkdownSection(t, level+1, ['lorem ipsum']) for t in subsection_titles]
        subsections_d = dict([(ss.title, ss) for ss in subsections_l])

        # sanity check: Make SURE we don't have duplicate ss titles and hence fewer dict entries!
        self.assertEqual(len(subsections_l), len(subsections_d)) 
        section = MarkdownSection(title, level, content_l, subsections_d)
        self.assert_section_valid(section, title, level, content_l, subsections_d)
        s = str(section)
        all_lines = s.split('\n')
        content_strs = [str(me) for me in content_l]
        subsections_strs = [f"""<a id="{to_id(key)}"></a>\n\n{ms}\n""" for key, ms in subsections_d.items()]
        exp_content = f"{'#'*level} {title}\n\n{'\n'.join(content_strs)}\n{'\n'.join(subsections_strs)}".split('\n')
        self.assertEqual(exp_content, all_lines, f"exp_content = <{exp_content}>, all_lines = <{all_lines}>")

if __name__ == "__main__":
    unittest.main()