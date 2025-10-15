# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from prettytable import HRuleStyle

from piplicenses.output import create_licenses_table, factory_styled_table_with_args
from tests import PatchDistributionsTestCase


class CreateLicensesTableTestCase(PatchDistributionsTestCase):
    @classmethod
    def check_rst(cls, text: str) -> None:
        parser = Parser()
        settings = get_default_settings(parser)
        settings.halt_level = 3
        document = new_document("<rst-doc>", settings=settings)
        parser.parse(text, document)

    def test_format_markdown(self) -> None:
        format_markdown_args = ["--format=markdown"]
        args = self.parser.parse_args(format_markdown_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("|", table.junction_char)
        self.assertEqual(HRuleStyle.HEADER, table.hrules)

    def test_format_rst_without_filter(self) -> None:
        self._patch_distributions()
        format_rst_args = ["--format=rst"]
        args = self.parser.parse_args(format_rst_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.ALL, table.hrules)

    def test_format_rst_default_filter(self) -> None:
        self._patch_distributions()
        format_rst_args = ["--format=rst", "--filter-strings"]
        args = self.parser.parse_args(format_rst_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.ALL, table.hrules)
        self.check_rst(str(table))

    def test_format_confluence(self) -> None:
        format_confluence_args = ["--format=confluence"]
        args = self.parser.parse_args(format_confluence_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("|", table.junction_char)
        self.assertEqual(HRuleStyle.NONE, table.hrules)


class FactoryStyledTableWithArgsTestCase(PatchDistributionsTestCase):
    def test_format_plain(self) -> None:
        format_plain_args = ["--format=plain"]
        args = self.parser.parse_args(format_plain_args)
        table = factory_styled_table_with_args(args)

        self.assertIn("l", table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.FRAME, table.hrules)
