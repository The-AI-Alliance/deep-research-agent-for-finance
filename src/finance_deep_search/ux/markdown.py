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
    def __init__(self, **properties: {str,str}):
        self.properties = properties
        self.title = properties.get('title', properties.get('name', ''))

    def __str__(self) -> str:
        pass

class MarkdownSection(MarkdownElement):
    def __init__(self, level: int, title: str, lines: list[str], **properties: dict[str,str]):
        super().__init__(title=title, **properties)
        self.level = level
        self.lines = lines

    def __str__(self) -> str:
        lines_str = '' if len(self.lines) == 0 else f"\n\n{'\n'.join(self.lines)}"
        return f"{self.level*'#'} {self.title}{lines_str}\n"

class MarkdownTable(MarkdownElement):
    def __init__(self, columns: list[str] | list[tuple[str,str]] = [], **properties: dict[str,str]):
        super().__init__(**properties)
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
        if len(self.columns) == 0:
            return ''
        else:
            columns_str = self.__make_row(self.columns)
            columns_justifications_str = self.__make_row(self.columns_justifications)
            rows_strs = [ self.__make_row(row) for row in self.rows ]
            return f"{columns_str}\n{columns_justifications_str}\n{'\n'.join(rows_strs)}\n"

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


class MarkdownTree(MarkdownElement):
    """Whereas MarkdownTable wrapped str, here we need hierarchical data."""

    default_bullet = '*'
    default_indentation = '  '
    def __init__(self, value: str | int | float | MarkdownElement, bullet: str = None, indentation: str = None, **properties: dict[str,str]):
        super().__init__(**properties)
        self.children: [MarkdownTree] = []
        self.node = value
        if bullet and not MarkdownTree.validate_bullet(bullet):
            raise ValueError(f"Disallowed bullet value {bullet}. Must be '*', '-', a number, or a letter.")
        self.bullet = bullet
        self.indentation = indentation

    def add_children(self, children: [MarkdownElement], **properties: dict[str,str]):
        self.children.extend(children)

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
        lines = [f"{indent_str}{bullet} {self.node}"]
        for child in self.children:
            lines.extend(child.as_strs(level+1, parent_bullet, parent_indent))
        return lines
        #return [f"{indent_str}{line}" for line in lines]

    def __str__(self) -> str:
        return "\n".join(self.as_strs(0, self.bullet, self.indentation))

    number_re = re.compile(r'^\d+$')
    letter_re = re.compile(r'^\W$')

    def validate_bullet(bullet: str) -> bool:
        if bullet == '*' or bullet == '-' \
            or MarkdownTree.number_re.match(bullet) or MarkdownTree.letter_re.match(bullet):
            return True 
        else:
            return False

class MarkdownDeepOrchestratorMonitor():
    """Markdown-based monitor to expose all internal state of the Deep Orchestrator"""

    def __init__(self, orchestrator: DeepOrchestrator):
        self.orchestrator = orchestrator
        self.start_time = time.time()


async def markdown_main(
    args: argparse.Namespace, 
    config: DeepOrchestratorConfig,
    deep_search: DeepSearch):

    if args.noop:
        print(f"Inside markdown_main. Returning...")
        return
    else:
        raise Error("Markdown support TODO.")