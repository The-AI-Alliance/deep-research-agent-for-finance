# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys
from random import sample

from finance_deep_search.ux.markdown import MarkdownTree

from tests.utils import (
    no_linefeeds_text,
    nonempty_text,
    nonempty_no_linefeeds_text,
    make_n_samples
)

class TestMarkdownTree(unittest.TestCase):
    """
    Test the MarkdownTree class.
    """

    @given(no_linefeeds_text)
    def test_make_empty_tree(self, value: str):
        """
        Test a tree constructed with just a value has no children.
        """
        tree = MarkdownTree(value = value)
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.bullet, None)
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text, st.integers(min_value=1, max_value=10))
    def test_make_empty_tree_with_integer_bullet(self, value: str, bullet: int):
        """
        Test a tree constructed with an integer value, a bullet, and no children.
        """
        tree = MarkdownTree(value = value, bullet = str(bullet))
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.bullet, str(bullet))
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text, st.from_regex(r'^\W$', fullmatch=True))
    def test_make_empty_tree_with_letter_bullet(self, value: str, bullet: str):
        """
        Test a tree constructed with a value, a letter bullet, and no children.
        """
        tree = MarkdownTree(value = value, bullet = bullet)
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text, st.sampled_from(['*', '-']))
    def test_make_empty_tree_with_dash_or_star_bullet(self, value: str, bullet: str):
        """
        Test a tree constructed with a value, '*' or '-' as the bullet, and no children.
        """
        tree = MarkdownTree(value = value, bullet = bullet)
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text, st.sampled_from([' ', '    ', '\t', '\t\t']))
    def test_make_empty_tree_with_indentation(self, value: str, indent: str):
        """
        Test a tree constructed with a value, an indentation, and no children.
        """
        tree = MarkdownTree(value = value, indentation = indent)
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.bullet, None)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, indent)

    @given(no_linefeeds_text, no_linefeeds_text)
    def test_make_empty_tree_fails_with_invalid_bullet(self, value: str, bullet: str):
        """
        Verify that a tree constructed with an invalid bullet fails.
        """
        if not MarkdownTree.validate_bullet(bullet):
            with self.assertRaises(ValueError):
                MarkdownTree(value = value, bullet = bullet)

    @given(no_linefeeds_text, st.sampled_from(['*', '-']), st.lists(no_linefeeds_text))
    def test_make_empty_tree_fails_with_invalid_bullet(self, value: str, bullet: str, children: list[str]):
        """
        Verify that a tree constructed with an invalid bullet fails.
        """
        tree = MarkdownTree(value = value, bullet = bullet)
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, None)
        children = [MarkdownTree(value = c, bullet = bullet) for c in children]
        tree.add_children(children)
        self.assertEqual(tree.children, children)

    @given(no_linefeeds_text, st.sampled_from(['*', '-']), 
        st.sampled_from(['  ', '    ', '\t', '\t\t']), 
        st.lists(no_linefeeds_text, max_size=5), 
        st.lists(no_linefeeds_text, max_size=5))
    def test_str_returns_nested_bullet_points(self, value: str, bullet: str, indent: str, children: list[str], grand_children: list[str]):
        """
        Verify that str(tree) constructs the expected multi-line, nested bullet string.
        """
        tree = MarkdownTree(value = value, bullet = bullet, indentation = indent)
        self.assertEqual(tree.node, value)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, indent)
        children_trees = [MarkdownTree(value = c, bullet = bullet) for c in children]
        grand_children_trees = [MarkdownTree(value = c, bullet = bullet) for c in grand_children]
        tree.add_children(children_trees)
        self.assertEqual(tree.children, children_trees)
        for child in tree.children:
            child.add_children(grand_children_trees)
            self.assertEqual(child.children, grand_children_trees)

        s = str(tree)
        expected = [f"{bullet} {value}"]
        for c in children:
            expected.append(f"{indent}{bullet} {c}")
            for gc in grand_children:
                expected.append(f"{indent}{indent}{bullet} {gc}")
        expected_str = '\n'.join(expected)
        self.assertEqual(expected_str, s, f"expected_str:\n{expected_str}\nvs.\n{s}\n")

if __name__ == "__main__":
    unittest.main()