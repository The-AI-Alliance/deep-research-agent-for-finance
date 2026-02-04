# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, sys
from random import sample

from ux.markdown_elements import MarkdownTable

from tests.utils import (
    no_linefeeds_text,
    nonempty_text,
    no_linefeeds_nonempty_text,
    make_n_samples
)

class TestMarkdownTable(unittest.TestCase):
    """
    Test the MarkdownTable class.
    """

    def justifications(min_size: int = 5, max_size: int = 10):
        return st.lists(
            st.sampled_from(list(MarkdownTable.justifications)), 
            min_size=min_size, max_size=max_size)

    def make_columns_justifications(self, columns: list[str], justs_samples: list[str]) -> tuple[list[str],list[str]]:
        justs = make_n_samples(justs_samples, len(columns))
        cjs = []
        for i in range(len(columns)):
            cjs.append((columns[i], justs[i]))
        return cjs, justs

    def assert_consistent_sizes(self,
        columns: list[str],
        columns_justifications: list[str],
        rows: list[list[str]]):
        clen = len(columns)
        self.assertEqual(clen, len(columns_justifications))
        for row in rows:
            self.assertTrue(clen == len(row))

    def assert_header_rows(self,
        table: MarkdownTable, 
        exp_title: str, 
        exp_columns: list[str],
        exp_columns_justifications: list[str],
        exp_rows: list[list[str]]):
        self.assertEqual(exp_title, table.title)
        self.assert_consistent_sizes(exp_columns, exp_columns_justifications, exp_rows)
        self.assert_consistent_sizes(table.columns, table.columns_justifications, table.rows)
        self.assertEqual(len(exp_columns), len(table.columns))
        
        s = str(table)
        if len(exp_columns) == 0:
            self.assertEqual('', s)
        else:
            ecjs = []
            for i in range(len(exp_columns)):
                c = exp_columns[i]
                j = exp_columns_justifications[i]
                ecjs.append(MarkdownTable.justify(c, j))
            
            self.assertEqual(exp_columns, table.columns, f"<{exp_columns}> vs. <{table.columns}>")
            self.assertEqual(ecjs, table.columns_justifications, f"<{ecjs}> vs. <{table.columns_justifications}>")
            self.assertEqual(exp_rows, table.rows, f"<{exp_rows}> vs. <{table.rows}>")
            
            all_lines = s.split('\n')
            index = 0
            # skip blank lines:
            while len(all_lines[index]) == 0:
                index += 1
            if len(exp_title) > 0:
                self.assertEqual(f"**Table: {exp_title}**", all_lines[index], f"s = <{s}>")
                index += 2 # skip a blank line
            ecs_str = f"| {' | '.join(exp_columns)} |"
            self.assertEqual(ecs_str, all_lines[index], f"<{ecs_str}> vs. <{all_lines[index]}>? (whole string = <{s}>)")
            index += 1
            ecjs_str = f"| {' | '.join(ecjs)} |"
            self.assertEqual(ecjs_str, all_lines[index], f"<{ecjs_str}> == <{all_lines[index]}>? (whole string = <{s}>)")
            index += 1

            for i in range(len(exp_rows)):
                exp_row = exp_rows[i]
                row = table.rows[i]
                exp_row_str = '| ' + ' | '.join([str(cell) for cell in exp_row]) + ' |'
                self.assertEqual(exp_row_str, all_lines[index+i], f"{i}: <{exp_row_str}> == <{all_lines[index+i]}>?")

    @given(st.lists(no_linefeeds_text()), justifications(min_size=10, max_size=20))
    def test_justify_with_valid_values(self, columns: list[str], justs_samples: list[str | None]):
        """
        Verify that MarkdownTable.justify() correctly maps the allowed justification
        flags with the correct Markdown syntax.
        """
        justs = make_n_samples(justs_samples, len(columns))
        for i in range(len(columns)):
            col = columns[i]
            len_col = len(col)-2 if len(col) > 2 else 1
            exp_dashs = '-'*len_col
            just = MarkdownTable.justify(columns[i], justs[i])
            match justs[i]:
                case 'left' | '' | None:
                    self.assertEqual(f':{exp_dashs}-', just)
                case 'right':
                    self.assertEqual(f'-{exp_dashs}:', just)
                case 'center' | 'full':
                    self.assertEqual(f':{exp_dashs}:', just)
                case _:
                    raise ValueError(f"Unrecognized column 'justify' value: <{justs[i]}>")

    @given(nonempty_text())
    def test_justify_with_invalid_values(self, text: str):
        """
        Verify that MarkdownTable.justify() correctly raises errors for invalid values.
        """
        if text in MarkdownTable.justifications:
            MarkdownTable.justify('-----', text)
        else:
            with self.assertRaises(ValueError):
                MarkdownTable.justify('-----', text)
        for j in MarkdownTable.justifications:
            MarkdownTable.justify('-----', j)
            if j and len(j) > 0:  # skip None and ''
                with self.assertRaises(ValueError):
                    MarkdownTable.justify('-----', j+text)
                with self.assertRaises(ValueError):
                    MarkdownTable.justify('-----', text+j)

    @given(no_linefeeds_text())
    def test_make_empty_table_with_title(self, title: str):
        """
        Verify that a table constructed with a list of columns and default justifications
        is effectively an empty string when rendered.
        """
        table = MarkdownTable(title=title)
        self.assert_header_rows(table, title, [], [], [])
        self.assertEqual('', str(table))

    @given(st.lists(no_linefeeds_text()))
    def test_make_table_with_columns_that_default_to_left_justification(self, columns: list[str]):
        """
        Verify that a table constructed with a list of columns and default justifications
        is properly formed.
        """
        table = MarkdownTable(columns = columns)
        self.assert_header_rows(table, '', columns, ['left' for _ in columns], [])

    @given(st.lists(no_linefeeds_text()), justifications(min_size=10, max_size=20))
    def test_make_table_with_columns_with_justifications(self, columns: list[str], justs_samples: list[str | None]):
        """
        Verify that a table constructed with a list of columns and specified justifications
        is properly formed.
        """
        cjs, justs = self.make_columns_justifications(columns, justs_samples)
        table = MarkdownTable(columns = cjs)
        self.assert_header_rows(table, '', columns, justs, [])


    @given(no_linefeeds_text(), st.lists(no_linefeeds_text()), justifications(min_size=10, max_size=20))
    def test_make_table_with_columns_with_justifications(self, 
        title: str, columns: list[str], justs_samples: list[str | None]):
        """
        Verify that a table constructed with a title and a list of columns with justifications,
        but no rows is still rendered as an empty table string.
        """
        cjs, justs = self.make_columns_justifications(columns, justs_samples)
        table = MarkdownTable(title=title, columns = cjs)
        self.assert_header_rows(table, title, columns, justs, [])

    @given(st.lists(no_linefeeds_text()))
    def test_table_add_columns_that_default_to_left_justification(self, columns: list[str]):
        """
        Verify that add_columns with a list of columns and no specified justifications
        is properly formed.
        """
        table = MarkdownTable()
        justs = ['left' for _ in columns]
        table.add_columns(columns)
        self.assert_header_rows(table, '', columns, justs, [])
        more_columns = [f"{col}2" for col in columns]
        more_justs = ['left' for _ in more_columns]

        table.add_columns(more_columns)
        self.assert_header_rows(table, '', columns+more_columns, justs+more_justs, [])

    @given(st.lists(no_linefeeds_text()), justifications(min_size=10, max_size=20))
    def test_table_add_columns_with_justifications(self, columns: list[str], justs_samples: list[str | None]):
        """
        Verify that add_columns with a list of columns and no specified justifications
        is properly formed.
        """
        table = MarkdownTable()
        cjs, justs = self.make_columns_justifications(columns, justs_samples)
        table.add_columns(cjs)
        self.assert_header_rows(table, '', columns, justs, [])
        more_columns = [f"{col}2" for col in columns]
        more_cjs, more_justs = self.make_columns_justifications(more_columns, justs_samples)
        table.add_columns(more_cjs)
        self.assert_header_rows(table, '', columns+more_columns, justs+more_justs, [])

    @given(st.lists(no_linefeeds_text()), justifications(min_size=10, max_size=20), st.lists(no_linefeeds_nonempty_text(), min_size=1), st.integers(min_value = 1, max_value=10))
    def test_table_add_row_with_list_of_cells(self, columns: list[str], justs_samples: list[str | None], cell_samples: list[str], num_rows: int):
        """
        Verify that a table constructed with a list of columns and specified justifications,
        and then with rows added with all cells, is properly formed.
        """
        cjs, justs = self.make_columns_justifications(columns, justs_samples)
        table = MarkdownTable(columns = cjs)
        len_cols = len(columns)
        rows = []
        if len_cols > 0:
            self.assertTrue(len(cell_samples) > 0)
            for j in range(num_rows):
                row = make_n_samples(cell_samples, len_cols)
                rows.append(row)
                table.add_row(row)
        self.assert_header_rows(table, '', columns, justs, rows)

    @given(st.lists(no_linefeeds_nonempty_text()), justifications(min_size=10, max_size=20), st.lists(no_linefeeds_nonempty_text(), min_size=1), st.integers(min_value = 1, max_value=10))
    def test_table_add_row_with_list_of_tuples(self, columns: list[str], justs_samples: list[str | None], cell_samples: list[str], num_rows: int):
        """
        Verify that a table constructed with a list of columns and specified justifications,
        and then with rows added using (column,cell) pairs, is properly formed.
        """
        cjs, justs = self.make_columns_justifications(columns, justs_samples)
        table = MarkdownTable(columns = cjs)
        len_cols = len(columns)
        rows = []
        if len_cols > 0:
            self.assertTrue(len(cell_samples) > 0)
            for j in range(num_rows):
                sub_len = int(len_cols/2) if len_cols >= 2 else 1
                sample_cols = make_n_samples(columns, sub_len)
                sample_cells = make_n_samples(cell_samples, sub_len)
                row = [(sample_cols[i], sample_cells[i]) for i in range(sub_len)]
                table.add_row(row)
                rows.append(row)
        rows_lists = [table.row_dict_to_list(dict(row)) for row in rows]
        self.assert_header_rows(table, '', columns, justs, rows_lists)

    @given(st.lists(no_linefeeds_nonempty_text()), justifications(min_size=10, max_size=20), st.lists(no_linefeeds_nonempty_text(), min_size=1), st.integers(min_value = 1, max_value=10))
    def test_table_add_row_with_dict(self, columns: list[str], justs_samples: list[str | None], cell_samples: list[str], num_rows: int):
        """
        Verify that a table constructed with a list of columns and specified justifications,
        and then with rows added using (column,cell) pairs, is properly formed.
        """
        cjs, justs = self.make_columns_justifications(columns, justs_samples)
        table = MarkdownTable(columns = cjs)
        len_cols = len(columns)
        rows = []
        if len_cols > 0:
            self.assertTrue(len(cell_samples) > 0)
            for j in range(num_rows):
                sub_len = int(len_cols/2) if len_cols >= 2 else 1
                sample_cols = make_n_samples(columns, sub_len)
                sample_cells = make_n_samples(cell_samples, sub_len)
                row = dict([(sample_cols[i], sample_cells[i]) for i in range(sub_len)])
                table.add_row(row)
                rows.append(row)
        rows_lists = [table.row_dict_to_list(dict(row)) for row in rows]
        self.assert_header_rows(table, '', columns, justs, rows_lists)


    @given(st.lists(no_linefeeds_nonempty_text(), min_size=1), no_linefeeds_nonempty_text())
    def test_table_add_row_with_list_of_tuples_with_bad_keys_fails(self, columns: list[str], other_text: str):
        """
        Verify that calling add_row with a tuple containing an unknown column name
        as the first value raises an error.
        """
        table = MarkdownTable(columns = columns)
        set_columns = set(columns)
        if not other_text in set_columns:
            with self.assertRaises(ValueError):
                table.add_row([(other_text, 0)])

    @given(st.lists(no_linefeeds_nonempty_text(), min_size=1), no_linefeeds_nonempty_text())
    def test_table_add_row_with_dict_with_bad_keys_fails(self, columns: list[str], other_text: str):
        """
        Verify that calling add_row with a map containing an unknown column name
        as a key raises an error.
        """
        table = MarkdownTable(columns = columns)
        set_columns = set(columns)
        if not other_text in set_columns:
            with self.assertRaises(ValueError):
                table.add_row({other_text: 0})

    @given(st.lists(no_linefeeds_nonempty_text(), min_size=1), no_linefeeds_nonempty_text())
    def test_row_dict_to_list_with_valid_values(self, columns: list[str], other_text: str):
        """
        Verify that row_dict_to_list properly constructs a row with a partial set of valid keys.
        """
        table = MarkdownTable(columns = columns)
        sub_len = int(len(columns)/2)
        if sub_len == 0:
            sub_len = 1
        keys = make_n_samples(columns, sub_len)
        row_dict = dict([(key, key) for key in keys])
        set_columns = set(columns)
        exp_row = [name if name in keys else '' for name in columns]
        row = table.row_dict_to_list(row_dict)
        self.assertEqual(exp_row, row)

    @given(st.lists(no_linefeeds_nonempty_text(), min_size=1), no_linefeeds_nonempty_text())
    def test_row_dict_to_list_fails_with_invalid_values(self, columns: list[str], other_text: str):
        """
        Verify that row_dict_to_list raises an error if a key is not a recognized column name.
        """
        table = MarkdownTable(columns = columns)
        set_columns = set(columns)
        if not other_text in set_columns:
            with self.assertRaises(ValueError):
                table.row_dict_to_list({other_text: 0})

if __name__ == "__main__":
    unittest.main()