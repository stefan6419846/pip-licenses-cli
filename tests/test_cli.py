# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

import re
from contextlib import redirect_stderr
from enum import Enum
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryFile
from unittest import TestCase, mock

import tomli_w
from black.mode import auto
from piplicenses_lib import FromArg, __pkgname__

from piplicenses.cli import (
    create_output_string,
    create_parser,
    create_warn_string,
    enum_key_to_value,
    get_output_fields,
    get_sortby,
    load_config_from_file,
    output_colored,
    save_if_needs,
    value_to_enum_key,
)
from piplicenses.constants import TOML_SECTION_NAME
from tests import CaptureOutput, CommandLineTestCase


class CreateOutputStringTestCase(CommandLineTestCase):
    def test_format_html(self) -> None:
        format_html_args = ["--format=html", "--with-authors"]
        args = self.parser.parse_args(format_html_args)
        output_string = create_output_string(args)

        self.assertIn("<table>", output_string)
        self.assertIn("Jukka Lehtosalo &lt;jukka.lehtosalo@iki.fi&gt;", output_string)  # author of "mypy"

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

    def test_format_plain_vertical(self) -> None:
        format_plain_args = ["--format=plain-vertical", "--from=classifier"]
        args = self.parser.parse_args(format_plain_args)
        output_string = create_output_string(args)
        self.assertIsNotNone(re.search(r"pep8-naming\n\d+\.\d+\.\d+\nMIT License\n", output_string), output_string)


class ParserTestCase(TestCase):
    def _assert_system_exit_and_get_stderr(self, parameters: list[str]) -> str:
        parser = create_parser()
        stderr = StringIO()
        with self.assertRaises(expected_exception=SystemExit), redirect_stderr(stderr):
            parser.parse_args(parameters)
        return stderr.getvalue()

    def test_verify_args(self) -> None:
        # --with-license-file missing
        stderr = self._assert_system_exit_and_get_stderr(["--no-license-path"])
        for arg in ("--no-license-path", "--with-license-file"):
            self.assertIn(arg, stderr)

        stderr = self._assert_system_exit_and_get_stderr(["--with-notice-file"])
        for arg in ("--with-notice-file", "--with-license-file"):
            self.assertIn(arg, stderr)

        # --filter-strings missing
        stderr = self._assert_system_exit_and_get_stderr(["--filter-code-page=utf8"])
        for arg in ("--filter-code-page", "--filter-strings"):
            self.assertIn(arg, stderr)

        # invalid code-page
        stderr = self._assert_system_exit_and_get_stderr(["--filter-strings", "--filter-code-page=XX"])
        for arg in ("invalid code", "--filter-code-page"):
            self.assertIn(arg, stderr)

    def test_pyproject_toml_args_parsed_correctly(self) -> None:
        # We test that parameters of different types are deserialized correctly.
        pyproject_conf = {
            "tool": {
                TOML_SECTION_NAME: {
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

        # Create a temporary file and write the TOML string to it.
        with NamedTemporaryFile(suffix=".toml", delete=False) as temp_file:
            temp_file.write(toml_str.encode("utf-8"))
            temp_file.seek(0)

            parser = create_parser(temp_file.name)
            args = parser.parse_args([])

            tool_conf = pyproject_conf["tool"][TOML_SECTION_NAME]

            # Assert values are correctly parsed from toml.
            self.assertEqual(FromArg.CLASSIFIER, args.from_)
            self.assertEqual(tool_conf["summary"], args.summary)
            self.assertEqual(tool_conf["ignore-packages"], args.ignore_packages)
            self.assertEqual(tool_conf["fail-on"], args.fail_on)

            # Assert args are rewritable using cli.
            args = parser.parse_args(["--from=meta"])

            self.assertEqual(FromArg.META, args.from_)

            # All other values are parsed from toml.
            self.assertEqual(tool_conf["summary"], args.summary)
            self.assertEqual(tool_conf["ignore-packages"], args.ignore_packages)
            self.assertEqual(tool_conf["fail-on"], args.fail_on)


class LoadConfigFromFileTestCase(TestCase):
    def test_load_non_existent_file(self) -> None:
        with NamedTemporaryFile() as fd:
            pass
        self.assertDictEqual({}, load_config_from_file(fd.name))


class EnumTestCase(TestCase):
    def test_functions(self) -> None:
        class TestEnum(Enum):
            PLAIN = P = auto()
            JSON_LICENSE_FINDER = JLF = auto()

        self.assertEqual(TestEnum.PLAIN, TestEnum.P)
        self.assertEqual(TestEnum.JSON_LICENSE_FINDER, getattr(TestEnum, value_to_enum_key("jlf")))

        self.assertEqual("JLF", value_to_enum_key("jlf"))
        self.assertEqual("JSON_LICENSE_FINDER", value_to_enum_key("json-license-finder"))

        self.assertEqual("json-license-finder", enum_key_to_value(TestEnum.JSON_LICENSE_FINDER))
        self.assertEqual("plain", enum_key_to_value(TestEnum.PLAIN))


class SaveIfNeedsTestCase(TestCase):
    def test_output_file_success(self) -> None:
        def mocked_open(*args, **kwargs):
            return TemporaryFile("w")

        with mock.patch("piplicenses.cli.open", mocked_open), mock.patch("sys.exit"), CaptureOutput() as captured:
            save_if_needs("/foo/bar.txt", "license list")

        self.assertIn("created path: ", captured.stdout)
        self.assertEqual("", captured.stderr)

    def test_output_file_error(self) -> None:
        def mocked_open(*args, **kwargs):
            raise OSError

        with mock.patch("piplicenses.cli.open", mocked_open), mock.patch("sys.exit"), CaptureOutput() as captured:
            save_if_needs("/foo/bar.txt", "license list")

        self.assertEqual("", captured.stdout)
        self.assertIn("check path: ", captured.stderr)

    def test_output_file_none(self) -> None:
        with mock.patch("sys.exit"), CaptureOutput() as captured:
            save_if_needs(None, "license list")

        # stdout and stderr are expected not to be called.
        self.assertEqual("", captured.stdout)
        self.assertEqual("", captured.stderr)

    def test_output_file_content(self) -> None:
        with NamedTemporaryFile() as fd, mock.patch("sys.exit"), CaptureOutput() as captured:
            fd.close()

            save_if_needs(fd.name, "Hello World!")
            self.assertEqual("Hello World!\n", Path(fd.name).read_text())

            save_if_needs(fd.name, "Hello World!\n")
            self.assertEqual("Hello World!\n", Path(fd.name).read_text())

        self.assertEqual(f"created path: {fd.name}\n" * 2, captured.stdout)
        self.assertEqual("", captured.stderr)


class OutputColoredTestCase(TestCase):

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


class CreateWarnStringTestCase(CommandLineTestCase):
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

    def test_with_license_files_format_warning(self) -> None:
        args = self.parser.parse_args(["--format=html", "--with-license-files"])
        warn_string = create_warn_string(args)
        self.assertIn("Ignoring request to output multiple files due to unsupported output format.", warn_string)

        args = self.parser.parse_args(["--format=json", "--with-license-files"])
        warn_string = create_warn_string(args)
        self.assertNotIn("Ignoring request to output multiple files due to unsupported output format.", warn_string)


class GetSortbyTestCase(CommandLineTestCase):
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


class GetOutputFieldsTestCase(CommandLineTestCase):
    def test_with_license_files(self) -> None:
        for format_string in ["json", "plain-vertical"]:
            with self.subTest(format_string=format_string):
                args = self.parser.parse_args(["--with-license-files", f"--format={format_string}", "--with-notice-files", "--with-other-files"])
                fields = get_output_fields(args)
                self.assertEqual(
                    ["Name", "Version", "License", "LicenseFiles", "LicenseTexts", "NoticeFiles", "NoticeTexts", "OtherFiles", "OtherTexts"], fields
                )

        for format_string in ["plain", "csv", "html"]:
            with self.subTest(format_string=format_string):
                args = self.parser.parse_args(["--with-license-files", f"--format={format_string}", "--with-notice-files", "--with-other-files"])
                fields = get_output_fields(args)
                self.assertEqual(["Name", "Version", "License"], fields)

    def test_files_singular_plural(self) -> None:
        args = self.parser.parse_args(
            [
                "--with-license-file",
                "--format=json",
                "--with-notice-file",
                "--with-other-files",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseFile", "LicenseText", "NoticeFile", "NoticeText", "OtherFiles", "OtherTexts"], fields)

        args = self.parser.parse_args(
            [
                "--with-license-files",
                "--format=json",
                "--with-notice-files",
                "--with-other-files",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseFiles", "LicenseTexts", "NoticeFiles", "NoticeTexts", "OtherFiles", "OtherTexts"], fields)

    def test_no_license_path(self) -> None:
        args = self.parser.parse_args(
            [
                "--with-license-files",
                "--format=json",
                "--with-notice-files",
                "--with-other-files",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseFiles", "LicenseTexts", "NoticeFiles", "NoticeTexts", "OtherFiles", "OtherTexts"], fields)

        args = self.parser.parse_args(
            [
                "--with-license-files",
                "--format=json",
                "--with-notice-files",
                "--with-other-files",
                "--no-license-path",
            ]
        )
        fields = get_output_fields(args)
        self.assertEqual(["Name", "Version", "License", "LicenseTexts", "NoticeTexts", "OtherTexts"], fields)
