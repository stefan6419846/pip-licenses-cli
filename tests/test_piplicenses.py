from __future__ import annotations

import copy
import email
import os
import re
import sys
import tempfile
import unittest
import venv
from enum import Enum, auto
from importlib.metadata import Distribution
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import docutils.frontend
import docutils.parsers.rst
import docutils.utils
import piplicenses_lib
import pytest
import tomli_w
from prettytable import HRuleStyle
from pytest import CaptureFixture, MonkeyPatch

try:
    import license_expression
except ImportError:
    license_expression = None  # type: ignore[assignment]

import piplicenses
from piplicenses import (
    DEFAULT_OUTPUT_FIELDS,
    SYSTEM_PACKAGES,
    CompatibleArgumentParser,
    FromArg,
    PipLicensesWarning,
    __pkgname__,
    _get_spdx_parser,
    case_insensitive_partial_match_set_diff,
    case_insensitive_partial_match_set_intersect,
    case_insensitive_set_diff,
    case_insensitive_set_intersect,
    create_licenses_table,
    create_output_string,
    create_parser,
    create_warn_string,
    enum_key_to_value,
    factory_styled_table_with_args,
    get_output_fields,
    get_packages,
    get_sortby,
    load_config_from_file,
    output_colored,
    save_if_needs,
    value_to_enum_key,
)

if TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from importlib.metadata._meta import PackageMetadata
    else:
        from email.message import Message as PackageMetadata


TESTS_PATH = Path(__file__).resolve().parent
FIXTURES_PATH = TESTS_PATH / "fixtures"

# Read from external file considering a terminal that cannot handle "emoji"
UNICODE_APPENDIX = (
    FIXTURES_PATH.joinpath("unicode_characters.txt")
    .read_text(encoding="utf-8")
    .replace("\n", "")
)

CRYPTOGRAPHY_VERSION = Distribution.from_name("cryptography").version

importlib_metadata_distributions_orig = (
    piplicenses_lib.importlib_metadata.distributions
)


def importlib_metadata_distributions_mocked(
    *args: Any, **kwargs: Any
) -> list[Distribution]:
    class DistributionMocker(Distribution):
        def __init__(self, orig_dist: Distribution) -> None:
            self.__dist = orig_dist

        @property
        def metadata(self) -> PackageMetadata:
            return EmailMessageMocker(self.__dist.metadata)

        def locate_file(self, path: str | os.PathLike[str]):
            return self.__dist.locate_file(path)

        def read_text(self, filename) -> str | None:
            return self.__dist.read_text(filename)

    class EmailMessageMocker(email.message.Message):
        def __init__(self, orig_msg: PackageMetadata) -> None:
            self.__msg = orig_msg

        def __getattr__(self, attr: str) -> Any:
            return getattr(self.__msg, attr)

        def __getitem__(self, key: str) -> Any:
            if key.lower() == "name":
                return self.__msg["name"] + " " + UNICODE_APPENDIX
            return self.__msg[key]

    packages = list(importlib_metadata_distributions_orig(*args, **kwargs))
    packages[-1] = DistributionMocker(packages[-1])  # type: ignore[abstract]
    return packages


class CommandLineTestCase(unittest.TestCase):
    parser = create_parser()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.parser = create_parser()


class TestGetLicenses(CommandLineTestCase):
    def _create_pkg_name_columns(self, table):
        index = DEFAULT_OUTPUT_FIELDS.index("Name")

        # XXX: access to private API
        rows = copy.deepcopy(table.rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    def _create_license_columns(self, table, output_fields):
        index = output_fields.index("License")

        # XXX: access to private API
        rows = copy.deepcopy(table.rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    # from https://stackoverflow.com/questions/12883428/ ...
    # ... how-to-parse-restructuredtext-in-python
    @staticmethod
    def check_rst(text: str) -> None:
        parser = docutils.parsers.rst.Parser()
        settings = docutils.frontend.get_default_settings(
            docutils.parsers.rst.Parser
        )
        settings.halt_level = 3
        document = docutils.utils.new_document("<rst-doc>", settings=settings)
        parser.parse(text, document)

    def test_with_empty_args(self) -> None:
        empty_args: list[str] = []
        args = self.parser.parse_args(empty_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.FRAME, table.hrules)

        output_fields = get_output_fields(args)
        self.assertEqual(
            output_fields, list(DEFAULT_OUTPUT_FIELDS) + ["License"]
        )
        self.assertNotIn("Author", output_fields)
        self.assertNotIn("URL", output_fields)

        pkg_name_columns = self._create_pkg_name_columns(table)
        for sys_pkg in SYSTEM_PACKAGES:
            self.assertNotIn(sys_pkg, pkg_name_columns)

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)

        output_string = create_output_string(args)
        self.assertNotIn("<table>", output_string)

    def test_from_meta(self) -> None:
        from_args = ["--from=meta"]
        args = self.parser.parse_args(from_args)

        output_fields = get_output_fields(args)
        self.assertIn("License", output_fields)

        table = create_licenses_table(args, output_fields)
        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_meta = "MIT"
        self.assertIn(license_notation_as_meta, license_columns)

    def test_with_spdx_license_in_meta(self) -> None:
        from_args = ["--from=meta"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License", output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_classifier = "Apache-2.0 OR BSD-3-Clause"
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_classifier(self) -> None:
        from_args = ["--from=classifier"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License", output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        license_notation_as_classifier = "MIT License"
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_mixed(self) -> None:
        from_args = ["--from=mixed"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License", output_fields)

        license_columns = self._create_license_columns(table, output_fields)
        # Depending on the condition "MIT" or "BSD" etc.
        license_notation_as_classifier = "MIT License"
        self.assertIn(license_notation_as_classifier, license_columns)

    def test_from_all(self) -> None:
        from_args = ["--from=all"]
        args = self.parser.parse_args(from_args)
        output_fields = get_output_fields(args)
        table = create_licenses_table(args, output_fields)

        self.assertIn("License-Metadata", output_fields)
        self.assertIn("License-Classifier", output_fields)

        index_license_meta = output_fields.index("License-Metadata")
        license_meta = []
        for row in table.rows:
            license_meta.append(row[index_license_meta])

        index_license_classifier = output_fields.index("License-Classifier")
        license_classifier = []
        for row in table.rows:
            license_classifier.append(row[index_license_classifier])

        for license_name in ("BSD", "MIT", "Apache 2.0"):
            self.assertIn(license_name, license_meta)
        for license_name in (
            "BSD License",
            "MIT License",
            "Apache Software License",
        ):
            self.assertIn(license_name, license_classifier)

    def test_with_system(self) -> None:
        with_system_args = ["--with-system"]
        args = self.parser.parse_args(with_system_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        pkg_names = list(
            map(piplicenses_lib.normalize_package_name, pkg_name_columns)
        )
        external_sys_pkgs = list(SYSTEM_PACKAGES)
        external_sys_pkgs.remove(__pkgname__)
        for sys_pkg in external_sys_pkgs:
            self.assertIn(sys_pkg, pkg_names)

    def test_with_authors(self) -> None:
        with_authors_args = ["--with-authors"]
        args = self.parser.parse_args(with_authors_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("Author", output_fields)

        output_string = create_output_string(args)
        self.assertIn("Author", output_string)

    def test_with_maintainers(self) -> None:
        with_maintainers_args = ["--with-maintainers"]
        args = self.parser.parse_args(with_maintainers_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("Maintainer", output_fields)

        output_string = create_output_string(args)
        self.assertIn("Maintainer", output_string)

    def test_with_urls(self) -> None:
        with_urls_args = ["--with-urls"]
        args = self.parser.parse_args(with_urls_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("URL", output_fields)

        output_string = create_output_string(args)
        self.assertIn("URL", output_string)

    def test_with_description(self) -> None:
        with_description_args = ["--with-description"]
        args = self.parser.parse_args(with_description_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("Description", output_fields)

        output_string = create_output_string(args)
        self.assertIn("Description", output_string)

    def test_without_version(self) -> None:
        without_version_args = ["--no-version"]
        args = self.parser.parse_args(without_version_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn("Version", output_fields)

        output_string = create_output_string(args)
        self.assertNotIn("Version", output_string)

    def test_with_license_file(self) -> None:
        with_license_file_args = ["--with-license-file"]
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("LicenseFile", output_fields)
        self.assertIn("LicenseText", output_fields)
        self.assertNotIn("NoticeFile", output_fields)
        self.assertNotIn("NoticeText", output_fields)

        output_string = create_output_string(args)
        self.assertIn("LicenseFile", output_string)
        self.assertIn("LicenseText", output_string)
        self.assertNotIn("NoticeFile", output_string)
        self.assertNotIn("NoticeText", output_string)

    def test_with_notice_file(self) -> None:
        with_license_file_args = ["--with-license-file", "--with-notice-file"]
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertIn("LicenseFile", output_fields)
        self.assertIn("LicenseText", output_fields)
        self.assertIn("NoticeFile", output_fields)
        self.assertIn("NoticeText", output_fields)

        output_string = create_output_string(args)
        self.assertIn("LicenseFile", output_string)
        self.assertIn("LicenseText", output_string)
        self.assertIn("NoticeFile", output_string)
        self.assertIn("NoticeText", output_string)

    def test_with_license_file_no_path(self) -> None:
        with_license_file_args = [
            "--with-license-file",
            "--with-notice-file",
            "--no-license-path",
        ]
        args = self.parser.parse_args(with_license_file_args)

        output_fields = get_output_fields(args)
        self.assertNotEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS))
        self.assertNotIn("LicenseFile", output_fields)
        self.assertIn("LicenseText", output_fields)
        self.assertNotIn("NoticeFile", output_fields)
        self.assertIn("NoticeText", output_fields)

        output_string = create_output_string(args)
        self.assertNotIn("LicenseFile", output_string)
        self.assertIn("LicenseText", output_string)
        self.assertNotIn("NoticeFile", output_string)
        self.assertIn("NoticeText", output_string)

    def test_with_license_file_warning(self) -> None:
        with_license_file_args = ["--with-license-file", "--format=markdown"]
        args = self.parser.parse_args(with_license_file_args)

        warn_string = create_warn_string(args)
        self.assertIn("best paired with --format=json", warn_string)

    def test_ignore_packages(self) -> None:
        ignore_pkg_name = "prettytable"
        ignore_packages_args = [
            "--ignore-package=" + ignore_pkg_name,
            "--with-system",
        ]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertNotIn(ignore_pkg_name, pkg_name_columns)

    def test_ignore_normalized_packages(self) -> None:
        ignore_pkg_name = "pip-licenses"
        ignore_packages_args = [
            "--ignore-package=pip_licenses",
            "--with-system",
        ]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertNotIn(ignore_pkg_name, pkg_name_columns)

    def test_ignore_packages_and_version(self) -> None:
        # Fictitious version that does not exist
        ignore_pkg_name = "prettytable"
        ignore_pkg_spec = ignore_pkg_name + ":1.99.99"
        ignore_packages_args = [
            "--ignore-package=" + ignore_pkg_spec,
            "--with-system",
        ]
        args = self.parser.parse_args(ignore_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        # It is expected that prettytable will include
        self.assertIn(ignore_pkg_name, pkg_name_columns)

    def test_with_packages(self) -> None:
        pkg_name = "py"
        only_packages_args = ["--packages=" + pkg_name]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_with_normalized_packages(self) -> None:
        pkg_name = "typing_extensions"
        only_packages_args = [
            "--package=typing-extensions",
            "--with-system",
        ]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_with_packages_with_system(self) -> None:
        pkg_name = "prettytable"
        only_packages_args = ["--packages=" + pkg_name, "--with-system"]
        args = self.parser.parse_args(only_packages_args)
        table = create_licenses_table(args)

        pkg_name_columns = self._create_pkg_name_columns(table)
        self.assertListEqual([pkg_name], pkg_name_columns)

    def test_order_name(self) -> None:
        order_name_args = ["--order=name"]
        args = self.parser.parse_args(order_name_args)

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)

    def test_order_license(self) -> None:
        order_license_args = ["--order=license"]
        args = self.parser.parse_args(order_license_args)

        sortby = get_sortby(args)
        self.assertEqual("License", sortby)

    def test_order_author(self) -> None:
        order_author_args = ["--order=author", "--with-authors"]
        args = self.parser.parse_args(order_author_args)

        sortby = get_sortby(args)
        self.assertEqual("Author", sortby)

    def test_order_maintainer(self) -> None:
        order_maintainer_args = ["--order=maintainer", "--with-maintainers"]
        args = self.parser.parse_args(order_maintainer_args)

        sortby = get_sortby(args)
        self.assertEqual("Maintainer", sortby)

    def test_order_url(self) -> None:
        order_url_args = ["--order=url", "--with-urls"]
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEqual("URL", sortby)

    def test_order_url_no_effect(self) -> None:
        order_url_args = ["--order=url"]
        args = self.parser.parse_args(order_url_args)

        sortby = get_sortby(args)
        self.assertEqual("Name", sortby)

    def test_format_plain(self) -> None:
        format_plain_args = ["--format=plain"]
        args = self.parser.parse_args(format_plain_args)
        table = factory_styled_table_with_args(args)

        self.assertIn("l", table.align.values())
        self.assertFalse(table.border)
        self.assertTrue(table.header)
        self.assertEqual("+", table.junction_char)
        self.assertEqual(HRuleStyle.FRAME, table.hrules)

    def test_format_plain_vertical(self) -> None:
        format_plain_args = ["--format=plain-vertical", "--from=classifier"]
        args = self.parser.parse_args(format_plain_args)
        output_string = create_output_string(args)
        self.assertIsNotNone(
            re.search(r"pytest\n\d\.\d\.\d\nMIT License\n", output_string)
        )

    def test_format_markdown(self) -> None:
        format_markdown_args = ["--format=markdown"]
        args = self.parser.parse_args(format_markdown_args)
        table = create_licenses_table(args)

        self.assertIn("l", table.align.values())
        self.assertTrue(table.border)
        self.assertTrue(table.header)
        self.assertEqual("|", table.junction_char)
        self.assertEqual(HRuleStyle.HEADER, table.hrules)

    def _patch_distributions(self) -> None:
        def cleanup():
            piplicenses_lib.importlib_metadata.distributions = (
                importlib_metadata_distributions_orig
            )

        self.addCleanup(cleanup)
        piplicenses_lib.importlib_metadata.distributions = (
            importlib_metadata_distributions_mocked
        )

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

    def test_format_html(self) -> None:
        format_html_args = ["--format=html", "--with-authors"]
        args = self.parser.parse_args(format_html_args)
        output_string = create_output_string(args)

        self.assertIn("<table>", output_string)
        self.assertIn("Filipe La&#237;ns", output_string)  # author of "build"

    def test_format_json(self) -> None:
        format_json_args = ["--format=json", "--with-authors"]
        args = self.parser.parse_args(format_json_args)
        output_string = create_output_string(args)

        self.assertIn('"Author":', output_string)
        self.assertNotIn('"URL":', output_string)

    def test_format_json_license_manager(self) -> None:
        format_json_args = ["--format=json-license-finder"]
        args = self.parser.parse_args(format_json_args)
        output_string = create_output_string(args)

        self.assertNotIn('"URL":', output_string)
        self.assertIn('"name":', output_string)
        self.assertIn('"version":', output_string)
        self.assertIn('"licenses":', output_string)

    def test_format_csv(self) -> None:
        format_csv_args = ["--format=csv", "--with-authors"]
        args = self.parser.parse_args(format_csv_args)
        output_string = create_output_string(args)

        obtained_header = output_string.split("\n", 1)[0]
        expected_header = '"Name","Version","License","Author"'
        self.assertEqual(obtained_header, expected_header)

    def test_summary(self) -> None:
        summary_args = ["--summary"]
        args = self.parser.parse_args(summary_args)
        output_string = create_output_string(args)

        self.assertIn("Count", output_string)
        self.assertNotIn("Name", output_string)

        warn_string = create_warn_string(args)
        self.assertEqual("", warn_string)

    def test_summary_sort_by_count(self) -> None:
        summary_args = ["--summary", "--order=count"]
        args = self.parser.parse_args(summary_args)

        sortby = get_sortby(args)
        self.assertEqual("Count", sortby)

    def test_summary_sort_by_name(self) -> None:
        summary_args = ["--summary", "--order=name"]
        args = self.parser.parse_args(summary_args)

        sortby = get_sortby(args)
        self.assertEqual("License", sortby)

    def test_summary_warning(self) -> None:
        summary_args = ["--summary", "--with-authors"]
        args = self.parser.parse_args(summary_args)

        warn_string = create_warn_string(args)
        self.assertIn(
            "using --with-authors and --with-urls will be ignored.",
            warn_string,
        )

        summary_args = ["--summary", "--with-urls"]
        args = self.parser.parse_args(summary_args)

        warn_string = create_warn_string(args)
        self.assertIn(
            "using --with-authors and --with-urls will be ignored.",
            warn_string,
        )

    def test_output_colored_normal(self) -> None:
        color_code = "32"
        text = __pkgname__
        actual = output_colored(color_code, text)

        self.assertTrue(actual.startswith("\033[32"))
        self.assertIn(text, actual)
        self.assertTrue(actual.endswith("\033[0m"))

    def test_output_colored_bold(self) -> None:
        color_code = "32"
        text = __pkgname__
        actual = output_colored(color_code, text, is_bold=True)

        self.assertTrue(actual.startswith("\033[1;32"))
        self.assertIn(text, actual)
        self.assertTrue(actual.endswith("\033[0m"))

    def test_without_filter(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args([])
        packages = list(piplicenses.get_packages(args))
        self.assertIn(UNICODE_APPENDIX, packages[-1].name)

    def test_with_default_filter(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args(["--filter-strings"])
        packages = list(piplicenses.get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1].name)

    def test_with_default_filter_and_license_file(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args(
            ["--filter-strings", "--with-license-file"]
        )
        packages = list(piplicenses.get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1].name)

    def test_with_specified_filter(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args(
            ["--filter-strings", "--filter-code-page=ascii"]
        )
        packages = list(piplicenses.get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1].summary)

    def test_case_insensitive_set_diff(self) -> None:
        set_a = {"MIT License"}
        set_b = {"Mit License", "BSD License"}
        set_c = {"mit license"}
        a_diff_b = case_insensitive_set_diff(set_a, set_b)
        a_diff_c = case_insensitive_set_diff(set_a, set_c)
        b_diff_c = case_insensitive_set_diff(set_b, set_c)
        a_diff_empty = case_insensitive_set_diff(set_a, set())

        self.assertSetEqual(set(), a_diff_b)
        self.assertSetEqual(set(), a_diff_c)
        self.assertIn("BSD License", b_diff_c)
        self.assertIn("MIT License", a_diff_empty)

    def test_case_insensitive_set_intersect(self) -> None:
        set_a = {"Revised BSD"}
        set_b = {"Apache License", "revised BSD"}
        set_c = {"revised bsd"}
        a_intersect_b = case_insensitive_set_intersect(set_a, set_b)
        a_intersect_c = case_insensitive_set_intersect(set_a, set_c)
        b_intersect_c = case_insensitive_set_intersect(set_b, set_c)
        a_intersect_empty = case_insensitive_set_intersect(set_a, set())

        self.assertSetEqual(set_a, a_intersect_b)
        self.assertSetEqual(set_a, a_intersect_c)
        self.assertSetEqual({"revised BSD"}, b_intersect_c)
        self.assertSetEqual(set(), a_intersect_empty)

    def test_case_insensitive_partial_match_set_diff(self) -> None:
        set_a = {"MIT License"}
        set_b = {"Mit", "BSD License"}
        set_c = {"mit license"}
        a_diff_b = case_insensitive_partial_match_set_diff(set_a, set_b)
        a_diff_c = case_insensitive_partial_match_set_diff(set_a, set_c)
        b_diff_c = case_insensitive_partial_match_set_diff(set_b, set_c)
        a_diff_empty = case_insensitive_partial_match_set_diff(set_a, set())

        self.assertSetEqual(set(), a_diff_b)
        self.assertSetEqual(set(), a_diff_c)
        self.assertIn("BSD License", b_diff_c)
        self.assertIn("MIT License", a_diff_empty)

    def test_case_insensitive_partial_match_set_intersect(self) -> None:
        set_a = {"Revised BSD"}
        set_b = {"Apache License", "revised BSD"}
        set_c = {"bsd"}
        a_intersect_b = case_insensitive_partial_match_set_intersect(
            set_a, set_b
        )
        a_intersect_c = case_insensitive_partial_match_set_intersect(
            set_a, set_c
        )
        b_intersect_c = case_insensitive_partial_match_set_intersect(
            set_b, set_c
        )
        a_intersect_empty = case_insensitive_partial_match_set_intersect(
            set_a, set()
        )

        self.assertSetEqual(set_a, a_intersect_b)
        self.assertSetEqual(set_a, a_intersect_c)
        self.assertSetEqual({"revised BSD"}, b_intersect_c)
        self.assertSetEqual(set(), a_intersect_empty)


def test_output_file_success(monkeypatch, capsys) -> None:
    def mocked_open(*args, **kwargs):
        return tempfile.TemporaryFile("w")

    monkeypatch.setattr(piplicenses, "open", mocked_open)
    monkeypatch.setattr(sys, "exit", lambda n: None)

    save_if_needs("/foo/bar.txt", "license list")
    captured = capsys.readouterr()
    assert "created path: " in captured.out
    assert "" == captured.err


def test_output_file_error(monkeypatch, capsys) -> None:
    def mocked_open(*args, **kwargs):
        raise IOError

    monkeypatch.setattr(piplicenses, "open", mocked_open)
    monkeypatch.setattr(sys, "exit", lambda n: None)

    save_if_needs("/foo/bar.txt", "license list")
    captured = capsys.readouterr()
    assert "" == captured.out
    assert "check path: " in captured.err


def test_output_file_none(monkeypatch, capsys) -> None:
    save_if_needs(None, "license list")
    captured = capsys.readouterr()

    # stdout and stderr are expected not to be called
    assert "" == captured.out
    assert "" == captured.err


def test_output_file_content(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "exit", lambda n: None)

    with tempfile.NamedTemporaryFile() as fd:
        fd.close()

        save_if_needs(fd.name, "Hello World!")
        assert Path(fd.name).read_text() == "Hello World!\n"

        save_if_needs(fd.name, "Hello World!\n")
        assert Path(fd.name).read_text() == "Hello World!\n"

    captured = capsys.readouterr()
    assert f"created path: {fd.name}\n" * 2 == captured.out
    assert "" == captured.err


def test_allow_only(monkeypatch, capsys) -> None:
    licenses = (
        "Bsd License",
        "Apache Software License",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "Python Software Foundation License",
        "Public Domain",
        "GNU General Public License (GPL)",
        "GNU Library or Lesser General Public License (LGPL)",
    )
    allow_only_args = ["--allow-only={}".format(";".join(licenses))]
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    captured = capsys.readouterr()
    assert "" == captured.out
    assert (
        "license MIT License not in allow-only licenses was found for "
        "package" in captured.err
    )


def test_allow_only_partial(monkeypatch, capsys) -> None:
    licenses = (
        "Bsd",
        "Apache",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "Python Software Foundation License",
        "Public Domain",
        "GNU General Public License (GPL)",
        "GNU Library or Lesser General Public License (LGPL)",
    )
    allow_only_args = [
        "--partial-match",
        "--allow-only={}".format(";".join(licenses)),
    ]
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    captured = capsys.readouterr()
    assert "" == captured.out
    assert (
        "license MIT License not in allow-only licenses was found for "
        "package" in captured.err
    )


def test_different_python() -> None:
    import tempfile

    class TempEnvBuild(venv.EnvBuilder):
        def post_setup(self, context: SimpleNamespace) -> None:
            self.context = context

    with tempfile.TemporaryDirectory() as target_dir_path:
        venv_builder = TempEnvBuild(with_pip=True)
        venv_builder.create(str(target_dir_path))
        python_exec = venv_builder.context.env_exe
        python_arg = f"--python={python_exec}"
        args = create_parser().parse_args([python_arg, "-s", "-f=json"])
        pkgs = get_packages(args)
        package_names = sorted(set(p.name for p in pkgs))
        print(package_names)

    expected_packages = ["pip"]
    if sys.version_info < (3, 12, 0):
        expected_packages.append("setuptools")
    assert package_names == expected_packages


def test_fail_on(monkeypatch: MonkeyPatch, capsys: CaptureFixture) -> None:
    licenses = ("MIT license",)
    allow_only_args = ["--fail-on={}".format(";".join(licenses))]
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    captured = capsys.readouterr()
    assert "" == captured.out
    assert "fail-on license MIT License was found for package" in captured.err


@pytest.mark.parametrize(
    "expression",
    ["Apache-2.0", "BSD-3-Clause"],
    ids=["Apache-2.0", "BSD-3-Clause"],
)
def test_spdx_operator_or_succeeds_if_either_license_is_allowed(
    expression: str,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture,
) -> None:
    # cryptography has an "Apache-2.0 OR BSD-3-Clause" license SPDX expression
    monkeypatch.setattr(sys, "exit", lambda n: None)
    spdx_args_success = [
        f"--allow-only={expression}",
        "--packages=cryptography",
    ]
    args = create_parser().parse_args(spdx_args_success)
    create_licenses_table(args)

    captured = capsys.readouterr()
    if license_expression is not None:
        assert captured.err == ""
    else:
        assert captured.err == (
            f"license Apache-2.0 OR BSD-3-Clause not in allow-only licenses"
            f" was found for package cryptography:{CRYPTOGRAPHY_VERSION}\n"
        )


@pytest.mark.parametrize(
    "expression",
    ["Apache-2.0", "BSD-3-Clause"],
    ids=["Apache-2.0", "BSD-3-Clause"],
)
def test_spdx_operator_or_fails_if_either_license_is_not_allowed(
    expression: str, monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    # cryptography has an "Apache-2.0 OR BSD-3-Clause" license SPDX expression
    monkeypatch.setattr(sys, "exit", lambda n: None)
    spdx_args_failure = [
        f"--fail-on={expression}",
        "--packages=cryptography",
    ]
    args = create_parser().parse_args(spdx_args_failure)
    create_licenses_table(args)

    captured = capsys.readouterr()
    if license_expression is None:
        assert captured.err == ""
    else:
        assert captured.err == (
            f"fail-on license {expression} was found for package "
            f"cryptography:{CRYPTOGRAPHY_VERSION}\n"
        )


@pytest.mark.parametrize(
    "expression",
    [
        "GPL-2.0-or-later WITH Bison-exception-2.2",
        "Apache-2.0 AND BSD-3-Clause",
        "Apache-2.0 OR BSD-3-Clause",
        "Hello World",
        "",
    ],
    ids=["SPDX WITH", "SPDX AND", "SPDX OR", "Invalid SPDX", "Empty"],
)
@pytest.mark.skipif(
    license_expression is not None,
    reason="Does not work with license-expression package.",
)
def test_spdx_parser(expression: str) -> None:
    assert _get_spdx_parser()(expression) == {expression}


@pytest.mark.parametrize(
    "expression,expected,should_warn",
    [
        (
            "GPL-2.0-or-later WITH Bison-exception-2.2",
            {"GPL-2.0-or-later WITH Bison-exception-2.2"},
            True,
        ),
        ("Apache-2.0 AND BSD-3-Clause", {"Apache-2.0 AND BSD-3-Clause"}, True),
        ("Apache-2.0 OR BSD-3-Clause", {"Apache-2.0", "BSD-3-Clause"}, False),
        ("Hello World", {"Hello World"}, False),
        ("", {""}, False),
    ],
    ids=["SPDX WITH", "SPDX AND", "SPDX OR", "Invalid SPDX", "Empty"],
)
@pytest.mark.skipif(
    license_expression is None, reason="Requires license-expression package."
)
def test_spdx_parser__license_expression(
    expression: str, expected: set[str], should_warn: bool
) -> None:
    if should_warn:
        with pytest.warns(PipLicensesWarning):
            assert _get_spdx_parser()(expression) == expected
    else:
        assert _get_spdx_parser()(expression) == expected


def test_fail_on_partial_match(monkeypatch, capsys) -> None:
    licenses = ("MIT",)
    allow_only_args = [
        "--partial-match",
        "--fail-on={}".format(";".join(licenses)),
    ]
    monkeypatch.setattr(sys, "exit", lambda n: None)
    args = create_parser().parse_args(allow_only_args)
    create_licenses_table(args)

    captured = capsys.readouterr()
    assert "" == captured.out
    assert (
        "fail-on license MIT License was found for " "package" in captured.err
    )


def test_enums() -> None:
    class TestEnum(Enum):
        PLAIN = P = auto()
        JSON_LICENSE_FINDER = JLF = auto()

    assert TestEnum.PLAIN == TestEnum.P
    assert (
        getattr(TestEnum, value_to_enum_key("jlf"))
        == TestEnum.JSON_LICENSE_FINDER
    )
    assert value_to_enum_key("jlf") == "JLF"
    assert value_to_enum_key("json-license-finder") == "JSON_LICENSE_FINDER"
    assert (
        enum_key_to_value(TestEnum.JSON_LICENSE_FINDER)
        == "json-license-finder"
    )
    assert enum_key_to_value(TestEnum.PLAIN) == "plain"


@pytest.fixture(scope="package")
def parser() -> CompatibleArgumentParser:
    return create_parser()


def test_verify_args(
    parser: CompatibleArgumentParser, capsys: CaptureFixture
) -> None:
    # --with-license-file missing
    with pytest.raises(SystemExit):
        parser.parse_args(["--no-license-path"])
    capture = capsys.readouterr().err
    for arg in ("--no-license-path", "--with-license-file"):
        assert arg in capture

    with pytest.raises(SystemExit):
        parser.parse_args(["--with-notice-file"])
    capture = capsys.readouterr().err
    for arg in ("--with-notice-file", "--with-license-file"):
        assert arg in capture

    # --filter-strings missing
    with pytest.raises(SystemExit):
        parser.parse_args(["--filter-code-page=utf8"])
    capture = capsys.readouterr().err
    for arg in ("--filter-code-page", "--filter-strings"):
        assert arg in capture

    # invalid code-page
    with pytest.raises(SystemExit):
        parser.parse_args(["--filter-strings", "--filter-code-page=XX"])
    capture = capsys.readouterr().err
    for arg in ("invalid code", "--filter-code-page"):
        assert arg in capture


def test_load_config_from_file():
    with tempfile.NamedTemporaryFile() as fd:
        pass
    assert load_config_from_file(fd.name) == {}


def test_pyproject_toml_args_parsed_correctly():
    # we test that parameters of different types are deserialized correctly
    pyproject_conf = {
        "tool": {
            __pkgname__: {
                # choices_from_enum
                "from": "classifier",
                # bool
                "summary": True,
                # list[str]
                "ignore-packages": ["package1", "package2"],
                # str
                "fail-on": "LIC1;LIC2",
            }
        }
    }

    toml_str = tomli_w.dumps(pyproject_conf)

    # Create a temporary file and write the TOML string to it
    with tempfile.NamedTemporaryFile(
        suffix=".toml", delete=False
    ) as temp_file:
        temp_file.write(toml_str.encode("utf-8"))
        temp_file.seek(0)

        parser = create_parser(temp_file.name)
        args = parser.parse_args([])

        tool_conf = pyproject_conf["tool"][__pkgname__]

        # assert values are correctly parsed from toml
        assert args.from_ == FromArg.CLASSIFIER
        assert args.summary == tool_conf["summary"]
        assert args.ignore_packages == tool_conf["ignore-packages"]
        assert args.fail_on == tool_conf["fail-on"]

        # assert args are rewritable using cli
        args = parser.parse_args(["--from=meta"])

        assert args.from_ != FromArg.CLASSIFIER
        assert args.from_ == FromArg.META

        # all other are parsed from toml
        assert args.summary == tool_conf["summary"]
        assert args.ignore_packages == tool_conf["ignore-packages"]
        assert args.fail_on == tool_conf["fail-on"]


def test_case_insensitive_partial_match_set_diff():
    set_a = {"Python", "Java", "C++"}
    set_b = {"Ruby", "JavaScript"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set_a
    ), "When no overlap, the result should be the same as set_a."

    set_a = {"Hello", "World"}
    set_b = {"hello", "world"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set()
    ), "When all items overlap, the result should be an empty set."

    set_a = {"HelloWorld", "Python", "JavaScript"}
    set_b = {"hello", "script"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {
        "Python"
    }, "Only 'Python' should remain as it has no overlap with set_b."

    set_a = {"HELLO", "world"}
    set_b = {"hello"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {
        "world"
    }, "The function should handle case-insensitive matches correctly."

    set_a = set()
    set_b = set()
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set()
    ), "When both sets are empty, the result should also be empty."

    set_a = {"Python", "Java"}
    set_b = set()
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set_a
    ), "If set_b is empty, result should be the same as set_a."

    set_a = set()
    set_b = {"Ruby"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert (
        result == set()
    ), "If set_a is empty, result should be empty regardless of set_b."

    set_a = {"Python 3.11", "Python 3.12", "Javascript"}
    set_b = {"Python", "Python 3"}
    result = case_insensitive_partial_match_set_diff(set_a, set_b)
    assert result == {"Javascript"}
