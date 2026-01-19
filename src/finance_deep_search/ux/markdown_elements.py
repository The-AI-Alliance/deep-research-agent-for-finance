#!/usr/bin/env python
"""
The Markdown-formatted streaming output version of Deep Orchestrator Finance Research Example
"""

import argparse
import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

from finance_deep_search.deep_search import DeepSearch

class MarkdownElement():
    """Super type of the other markdown-related types.
    Note: There are places in subtype method signatures where `MarkdownElement`
    is used, but really the type itself should be used. It appears that Python
    doesn't allow self-references to a type _while inside_ its definition!
    """
    def __init__(self, title: str = ''):
        self.title = title

    def __str__(self) -> str:
        return self.title

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, MarkdownElement):
            return False
        return self.title == other.title

class MarkdownSection(MarkdownElement):
    def __init__(self, 
        level: int,
        title: str,
        content: list[MarkdownElement | str] = [],
        subsections: dict[str,MarkdownElement] = {}):
        """
        Construct a Markdown section with heading level, title string, and an optional 
        list of lines for the initial content. For subsections, use `add_subsections`.
        The level >= 1, although numbers bigger than 6 or so don't make much sense.
        The title must be non-empty, since it is needed to render the section header.
        """
        super().__init__(title)
        assert title, "MarkdownSection titles can't be empty!"
        assert level > 0, f"Invalid level '{level}' (must be > 0)"
        self.level = level
        # we store the content in a map by keys and rely on the python Dict 
        # implementation feature that insertion order is preserved.
        self.content: list[MarkdownElement] = []
        self.subsections: list[MarkdownElement] = {}
        self.add_intro_lines(content)
        self.add_subsections(subsections)

    def set_intro_lines(self, content: list[MarkdownElement | str]) -> str:
        """
        Replace the lines (or elements like tables, ...) for the content at the top
        of the section. Note that subsections added using `add_subsections` 
        will be rendered _below_ the content at the top.
        """
        self.content = []
        self.add_intro_lines(content)

    def add_intro_lines(self, content: list[MarkdownElement | str]) -> str:
        """
        Add lines (or elements like tables, ...) to the content at the top
        of the section. Note that subsections added using `add_subsections` 
        will be rendered _below_ the content at the top.
        """
        for line in content:
            if type(line) is MarkdownElement:
                self.content.append(line)
            else:
                self.content.append(MarkdownElement(title=line))

    def set_subsections(self, subsections: dict[str,MarkdownElement] | list[MarkdownElement]):
        """
        Replace the subsections.
        """
        self.subsections = {}
        self.add_subsections(subsections)
        
    def add_subsections(self, subsections: dict[str,MarkdownElement] | list[MarkdownElement]):
        """
        Add subsections. They will be stored in a dictionary ordered by insertion order
        (a Python dict implementation feature...), which we need to support rendering in
        the correct order. So, insert the subsections in the correct order for displaying.
        Use a dict argument if you want to specify the keys. If you pass a list, the
        element titles will be used as the keys. Hence, use non-empty titles for any 
        subsections provided. (The declared type is `MarkdownElement`, but this is only
        because parsing doesn't work if you "self-reference" a type, e.g., `MarkdownSection`.)
        Storing in a dict allows subsequent updating of a subsection by referring to it by its
        key. Similarly, a `ValueError` is raised if any keys in the new subsections that
        already exist in the current subsections.
        """
        ss = subsections
        if type(subsections) is list:
            ss = dict([(s.title, s) for s in subsections])

        bad_keys = []
        bad_levels = []
        for key, s in ss.items():
            if key in self.subsections:
                bad_keys.append(key) 
            level = s.level
            if level <= self.level:
                bad_levels.append(level) 
        error = 'add_subsections():'
        if len(bad_keys) > 0:
            error += f" All new subsections must have a unique key. bad keys = {bad_keys}. Existing keys = <{self.subsections.keys()}>, new keys = <{ss.keys()}>"
        if len(bad_levels) > 0:
            error += f" All levels for new subsections must be > self.level ({self.level}). Bad levels = <{bad_levels}>."
        if len(bad_keys) > 0 or len(bad_levels) > 0:
            raise ValueError(
                f"add_subsections(): All new subsections must have a unique key. Existing keys = <{self.subsections.keys()}>. Attempted added keys = <{ss.keys()}>")

        self.subsections.update(ss)

    def clear(self):
        """Remove the leading content and subsections."""
        self.content = []
        self.subsections = {}

    def __setitem__(self, key: str, item: MarkdownElement):
        """
        Allow dictionary-like indexing of subsections.
        While you can replace a subsection this way, you can also just fetch
        the items with `my_section['foo']` and edit it directly.
        """
        self.subsections[key] = item

    def __getitem__(self, key: str) -> MarkdownElement:
        """
        Allow dictionary-like indexing of subsections.
        While you can replace a subsection this way, you can also just fetch
        the items with `my_section['foo']` and edit it directly.
        """
        return self.subsections[key]
 
    def __str__(self) -> str:
        content_str = '\n'.join([str(c) for c in self.content])
        subsections_str = '\n'.join([str(s) for s in self.subsections.values()])
        return f"{self.level*'#'} {self.title}\n\n{content_str}\n{subsections_str}"

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, MarkdownSection):
            return false
        return  self.level == other.level \
            and self.content == other.content \
            and self.subsections == other.subsections
        
class MarkdownTable(MarkdownElement):
    def __init__(self, title: str = '', columns: list[str] | list[tuple[str,str]] = []):
        super().__init__(title)
        self.columns: [str] = []
        self.columns_justifications: [str] = []
        self.rows = []
        self.add_columns(columns)

    def add_columns(self, columns: list[str] | list[tuple[str,str]]):
        """
        Append one or more columns to the list of columns.
        If the input is a list of strings, then they are the column names
        and all will be left justified.
        If the input is a list of two-tuples, then the first elements are 
        the column names and the second elements are the justification strings,
        where the allowed justification values are:
        * `left`   means left justification 
        * `center` means center justification 
        * `right`  means right justification 
        Left justification is the default, so `` and `None` 
        are interpreted as left justification.
        """
        if len(columns) == 0:
            return 
        match self.__which_type(columns):
            case 'list[str]':
                self.columns.extend(columns)
                self.columns_justifications.extend([MarkdownTable.justify(c, 'left') for c in columns])
            case 'list[tuple]':
                self.columns.extend([c[0] for c in columns])
                self.columns_justifications.extend([MarkdownTable.justify(c[0], c[1]) for c in columns])
            case s:
                raise ValueError(f"Bad type for input columns: {type(columns)} ('{s}' was returned by __which_types()) (columns = {columns})")

    def add_row(self, row: list[any] | list[tuple[str,any]] | dict[str,any]):
        """
        Add a row of values to the table.
        If a list of values is passed in, the number of values must match the number of columns!
        If a list of tuples or a dict is passed in, then the keys must be in the set of columns and
        empty values will be used for the unspecified cells.
        """

        match self.__which_type(row):
            case 'list[str]':
                if len(row) != len(self.columns):
                    raise ValueError(f"Wrong number of cells in row: {len(row)}. Expected {len(self.columns)}.")
                self.rows.append(row)
            case 'list[tuple]':
                self.rows.append(self.row_dict_to_list(dict(row)))
            case 'dict':
                self.rows.append(self.row_dict_to_list(row))

    def row_dict_to_list(self, row_dict: dict[str,any]) -> list[any]:
        # Check that no unknown columns are specified.
        names = set(self.columns)
        keys = set(row_dict.keys())
        if names.union(keys) != names:
            raise ValueError(f"At least one unexpected column name <{keys}> that isn't in the set of columns = <{names}>")
        new_row = [row_dict.get(name, '') for name in self.columns]
        return new_row

    justifications = {'left', 'center', 'full', 'right', '', None}

    def is_justification(value: str) -> bool:
        return value in MarkdownTable.justifications

    def justify(column_name: str, justification: str) -> str:
        if not MarkdownTable.is_justification(justification):
            raise ValueError(f"Unrecognized column 'justify' value: <{justification}> (column_name = <{column_name}>)")
        else:
            num_dashes = len(column_name) - 2 if len(column_name) > 2 else 1
            dashes = '-'*(num_dashes)
            match justification:
                case 'left' | '' | None:
                    return f':{dashes}-'
                case 'right':
                    return f'-{dashes}:'
                case 'center' | 'full':
                    return f':{dashes}:'

    def __str__(self) -> str:
        title_str = ''
        if len(self.title) > 0:
            title_str = f"Table {self.title}\n"

        if len(self.columns) == 0:
            return ''
        else:
            columns_str = self.__make_row(self.columns)
            columns_justifications_str = self.__make_row(self.columns_justifications)
            rows_strs = [ self.__make_row(row) for row in self.rows ]
            return f"{title_str}{columns_str}\n{columns_justifications_str}\n{'\n'.join(rows_strs)}\n"

    def __which_type(self, values: list[str] | list[tuple[str,any]] | dict[str,any]) -> str | None:
        def type_error():
            tcol  = f"type(values) = <{type(values)}>,"
            t0col = f"type(values[0]) = <{type(values[0])}>,"
            raise ValueError(f"Unexpected argument type: {tcol} {t0col} values = <{values}>")

        if len(values) == 0:
            return 0
        elif type(values) is list:
            t0 = type(values[0])
            if t0 is str:
                return 'list[str]'
            elif t0 is tuple:
                return 'list[tuple]'
            else:
                type_error()
        elif type(values) is dict:
            return 'dict'
        else:
            type_error()

    def __make_row(self, values: list[any]) -> str:
        if len(values) == 0:
            return '' 
        else:
            return f"| {' | '.join([str(v) for v in values])} |"

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, MarkdownTable):
            return false
        return  self.columns == other.columns \
            and self.columns_justifications == other.columns_justifications \
            and self.rows == other.rows
        

class MarkdownTree(MarkdownElement):
    """Whereas MarkdownTable wrapped str, here we need hierarchical data."""

    default_bullet = '*'
    default_indentation = '  '
    def __init__(self, 
        label: str | int | float, 
        bullet: str = None, 
        indentation: str = None):
        super().__init__(label)
        self.children: [MarkdownTree] = []
        self.label = label
        if bullet and not MarkdownTree.validate_bullet(bullet):
            raise ValueError(f"Disallowed bullet value {bullet}. Must be '*', '-', a number, or a letter.")
        self.bullet = bullet
        self.indentation = indentation

    def add(self, child: MarkdownElement | str):
        "Add a sub bullet."
        if type(child) is MarkdownTree:
            self.children.append(child)
        elif type(child) is MarkdownElement:
            self.children.append(child.title) # Will be converted it to MTree!
        else:
            self.children.append(MarkdownTree(str(child)))

    def add_children(self, children: list[MarkdownElement | str]):
        "Add multiple sub bullets."
        for child in children:
            self.add(child)

    def __tri(self, first: str | None, second: str | None, third: str) -> str:
        if first:
            return first
        elif second:
            return second
        else:
            return third

    def as_strs(self, level: int, parent_bullet: str, parent_indent: str) -> list[str]:
        bullet = self.__tri(self.bullet, parent_bullet, MarkdownTree.default_bullet)
        indent = self.__tri(self.indentation, parent_indent, MarkdownTree.default_indentation)
        indent_str = level*indent
        lines = [f"{indent_str}{bullet} {self.label}"]
        for child in self.children:
            lines.extend(child.as_strs(level+1, parent_bullet, parent_indent))
        return lines
        #return [f"{indent_str}{line}" for line in lines]

    def __str__(self) -> str:
        return "\n".join(self.as_strs(0, self.bullet, self.indentation))

    number_re = re.compile(r'^\d+$')
    letter_re = re.compile(r'^\W$')

    def get_bullet(self) -> str:
        return self.bullet if self.bullet else MarkdownTree.default_bullet

    def get_indentation(self) -> str:
        return self.indentation if self.indentation else MarkdownTree.default_indentation
        
    def validate_bullet(bullet: str) -> bool:
        if bullet == '*' or bullet == '-' \
            or MarkdownTree.number_re.match(bullet) or MarkdownTree.letter_re.match(bullet):
            return True 
        else:
            return False

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, MarkdownTree):
            return false
        return  self.label == other.label \
            and self.get_bullet() == other.get_bullet() \
            and self.get_indentation() == other.get_indentation() \
            and self.children == other.children 
