# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys
from random import sample

from ux.markdown_elements import MarkdownTree

from tests.utils import (
    no_linefeeds_text,
)

class TestMarkdownTree(unittest.TestCase):
    """
    Test the MarkdownTree class.
    """

    @given(no_linefeeds_text())
    def test_make_empty_tree(self, label: str):
        """
        Test a tree constructed with just a label has no children.
        """
        tree = MarkdownTree(label = label)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.bullet, None)
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text(), st.integers(min_value=1, max_value=10))
    def test_make_empty_tree_with_integer_bullet(self, label: str, bullet: int):
        """
        Test a tree constructed with an integer label, a bullet, and no children.
        """
        tree = MarkdownTree(label = label, bullet = str(bullet))
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.bullet, str(bullet))
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text(), st.from_regex(r'^\W$', fullmatch=True))
    def test_make_empty_tree_with_letter_bullet(self, label: str, bullet: str):
        """
        Test a tree constructed with a label, a letter bullet, and no children.
        """
        tree = MarkdownTree(label = label, bullet = bullet)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text(), st.sampled_from(['*', '-']))
    def test_make_empty_tree_with_dash_or_star_bullet(self, label: str, bullet: str):
        """
        Test a tree constructed with a label, '*' or '-' as the bullet, and no children.
        """
        tree = MarkdownTree(label = label, bullet = bullet)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, None)

    @given(no_linefeeds_text(), st.sampled_from([' ', '    ', '\t', '\t\t']))
    def test_make_empty_tree_with_indentation(self, label: str, indent: str):
        """
        Test a tree constructed with a label, an indentation, and no children.
        """
        tree = MarkdownTree(label = label, indentation = indent)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, None)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, indent)

    @given(no_linefeeds_text(), no_linefeeds_text())
    def test_make_empty_tree_fails_with_invalid_bullet(self, label: str, bullet: str):
        """
        Verify that a tree constructed with an invalid bullet fails.
        """
        if not MarkdownTree.validate_bullet(bullet):
            with self.assertRaises(ValueError):
                MarkdownTree(label = label, bullet = bullet)

    @given(no_linefeeds_text(), st.sampled_from(['*', '-']), st.lists(no_linefeeds_text()))
    def test_make_empty_tree_fails_with_invalid_bullet(self, label: str, bullet: str, children: list[str]):
        """
        Verify that a tree constructed with an invalid bullet fails.
        """
        tree = MarkdownTree(label = label, bullet = bullet)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, None)
        children = [MarkdownTree(label = c, bullet = bullet) for c in children]
        tree.add_children(children)
        self.assertEqual(tree.children, children)

    @given(no_linefeeds_text(), st.sampled_from(['*', '-']), 
        st.sampled_from(['  ', '    ', '\t', '\t\t']), 
        st.lists(no_linefeeds_text(), max_size=5), 
        st.lists(no_linefeeds_text(), max_size=5))
    def test_add_adds_one_nested_bullet_point(self, label: str, bullet: str, indent: str, children: list[str], grand_children: list[str]):
        """
        Verify that adding children works as expected.
        """
        tree = MarkdownTree(label = label, bullet = bullet, indentation = indent)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, indent)
        children_trees = [MarkdownTree(label = c, bullet = bullet) for c in children]
        grand_children_trees = [MarkdownTree(label = c, bullet = bullet) for c in grand_children]
        for child in children_trees:
            tree.add(child) 
        self.assertEqual(tree.children, children_trees)
        for child in tree.children:
            for grand_child in grand_children_trees:
                child.add(grand_child) 
            self.assertEqual(child.children, grand_children_trees)

    @given(no_linefeeds_text(), st.sampled_from(['*', '-']), 
        st.sampled_from(['  ', '    ', '\t', '\t\t']), 
        st.lists(no_linefeeds_text(), max_size=5), 
        st.lists(no_linefeeds_text(), max_size=5))
    def test_add_children_adds_nested_bullet_points(self, label: str, bullet: str, indent: str, children: list[str], grand_children: list[str]):
        """
        Verify that adding children works as expected.
        """
        tree = MarkdownTree(label = label, bullet = bullet, indentation = indent)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, indent)
        children_trees = [MarkdownTree(label = c, bullet = bullet) for c in children]
        grand_children_trees = [MarkdownTree(label = c, bullet = bullet) for c in grand_children]
        tree.add_children(children_trees)
        self.assertEqual(tree.children, children_trees)
        for child in tree.children:
            child.add_children(grand_children_trees)
            self.assertEqual(child.children, grand_children_trees)

    @given(no_linefeeds_text(), st.sampled_from(['*', '-']), 
        st.sampled_from(['  ', '    ', '\t', '\t\t']), 
        st.lists(no_linefeeds_text(), max_size=5), 
        st.lists(no_linefeeds_text(), max_size=5))
    def test_str_returns_nested_bullet_points(self, label: str, bullet: str, indent: str, children: list[str], grand_children: list[str]):
        """
        Verify that str(tree) constructs the expected multi-line, nested bullet string.
        """
        tree = MarkdownTree(label = label, bullet = bullet, indentation = indent)
        self.assertEqual(tree.label, label)
        self.assertEqual(tree.bullet, bullet)
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.indentation, indent)
        children_trees = [MarkdownTree(label = c, bullet = bullet) for c in children]
        grand_children_trees = [MarkdownTree(label = c) for c in grand_children]
        tree.add_children(children_trees)
        self.assertEqual(tree.children, children_trees)
        for child in tree.children:
            child.add_children(grand_children) # Note the strings are added...
            for i in range(len(grand_children)):
                self.assertEqual(child.children[i], grand_children_trees[i]) # ... but they are converted to trees

        s = str(tree)
        expected = [f"{bullet} {label}"]
        for c in children:
            expected.append(f"{indent}{bullet} {c}")
            for gc in grand_children:
                expected.append(f"{indent}{indent}{bullet} {gc}")
        expected_str = '\n'.join(expected)
        self.assertEqual(expected_str, s, f"expected_str:\n{expected_str}\nvs.\n{s}\n")

if __name__ == "__main__":
    unittest.main()