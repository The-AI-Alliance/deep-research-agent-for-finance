# Unit tests for the "prompt utils" module using Hypothesis for property-based testing.
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

from common.prompt_utils import (
    split_frontmatter_and_content,
    load_prompt_markdown,
)

class TestPromptUtils(unittest.TestCase):
    """
    Test the prompt-related utilities.
    """

    def check(self, frontmatter: str, content: str, text: str):
        """Ignore whitespace at the beginnings and the ends."""
        actual_frontmatter, actual_content = split_frontmatter_and_content(text)
        fm  = frontmatter.strip()
        afm = actual_frontmatter.strip()
        ct  = content.strip()
        act = actual_content.strip()
        self.assertEqual(fm, afm, 
            f'\nfrontmatter\n  expected: <{fm}>\n  actual: <{afm}>\n')
        self.assertEqual(ct, act,
            f'\ncontent\n  expected: <{ct}>\n  actual: <{act}>\n')

    @given(st.text(), st.text(), st.integers(min_value=3, max_value=10))
    def test_frontmatter_delimiters_have_three_or_more_dashes_before_and_after(self, 
        frontmatter: str, content: str, num_dashes: int):
        """
        Verify that the frontmatter and content are properly identified when
        the frontmatter block starts and ends with three or more dashes "-" on 
        separate lines. We ignore whitespace at the beginnings and the ends of strings.
        """
        delim = '-'*num_dashes
        text = f"{delim}\n{frontmatter}\n{delim}\n{content}"
        self.check(frontmatter, content, text)

    @given(st.text(), st.text(), st.sampled_from([1, 2]))
    def test_frontmatter_delimiters_with_one_or_two_dashes_are_treated_as_content(self, 
        frontmatter: str, content: str, num_dashes: int):
        """
        Verify that if the frontmatter delimiters have only one or two dashes, they
        and the text they enclose are considered part of the content and not treated
        as frontmatter. We ignore whitespace at the beginnings and the ends of strings.
        """
        delim = '-'*num_dashes
        text = f"{delim}\n{frontmatter}\n{delim}\n{content}"
        actual_frontmatter, actual_content = split_frontmatter_and_content(text)
        self.assertEqual(None, actual_frontmatter)
        self.assertEqual(text.split(), actual_content.split())

    @given(st.text(), st.text(), st.text())
    def test_content_before_the_frontmatter_is_ignored(self, 
        before_frontmatter: str, frontmatter: str, content: str):
        """
        Verify that any content appearing before the frontmatter block is ignored.
        We ignore whitespace at the beginnings and the ends of strings.
        """
        text = f"{before_frontmatter}\n---\n{frontmatter}\n---\n{content}"
        self.check(frontmatter, content, text)        

    @given(st.text(), st.text(), st.text())
    def test_content_before_the_frontmatter_is_ignored(self, 
        before_frontmatter: str, frontmatter: str, content: str):
        """
        Verify that any content appearing before the frontmatter block is ignored.
        We ignore whitespace at the beginnings and the ends of strings.
        """
        text = f"{before_frontmatter}\n---\n{frontmatter}\n---\n{content}"
        self.check(frontmatter, content, text)        

    @given(st.text(), st.text(), st.text())
    def test_extra_dash_delimited_content_is_not_parsed_as_frontmatter(self, 
        before_frontmatter: str, frontmatter: str, content: str):
        """
        Verify that if there is more than two frontmatter block delimiters, all but 
        the first two are treated as part of the content.
        We ignore whitespace at the beginnings and the ends of strings.
        """
        all_content1 = f'{content}\n---\nfoo'
        all_content2 = f'{content}\n---\nfoo\n---\nbar'
        text1 = f"{before_frontmatter}\n---\n{frontmatter}\n---\n{all_content1}"
        self.check(frontmatter, all_content1, text1)        
        text2 = f"{before_frontmatter}\n---\n{frontmatter}\n---\n{all_content2}"
        self.check(frontmatter, all_content2, text2)        

    @given(st.text(), st.text())
    def test_load_prompt_markdown_returns_the_content_only(self,
        frontmatter: str, content: str):
        """The frontmatter is removed from the returned content."""
        with open("temp_prompt.md", 'w', encoding='utf-8') as prompt_file:
            prompt_file.write('---\n')
            prompt_file.write(frontmatter)
            prompt_file.write('\n')
            prompt_file.write('---\n')
            prompt_file.write(content)
        prompt_test_file = Path("temp_prompt.md")
        actual_content = load_prompt_markdown(prompt_test_file)
        prompt_test_file.unlink()
        self.assertEqual(content, actual_content)

    def test_load_prompt_markdown_returns_the_content_only(self):
        """FileNotFoundError is raised if the file doesn't exist."""
        prompt_test_file = Path("does_not_exist.md")
        with self.assertRaises(FileNotFoundError):
            actual_content = load_prompt_markdown(prompt_test_file)


if __name__ == "__main__":
    unittest.main()