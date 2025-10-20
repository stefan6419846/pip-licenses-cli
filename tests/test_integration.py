# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

import copy
import json
import sys
import venv
from importlib.metadata import Distribution, PathDistribution
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from piplicenses_lib import PackageInfo, normalize_package_name
from prettytable import HRuleStyle, PrettyTable

from piplicenses import __pkgname__
from piplicenses.cli import create_output_string, create_parser, create_warn_string, get_output_fields, get_sortby
from piplicenses.collector import get_packages
from piplicenses.constants import DEFAULT_OUTPUT_FIELDS, SYSTEM_PACKAGES
from piplicenses.output import create_licenses_table
from tests import CaptureOutput, CommandLineTestCase

try:
    import license_expression
except ImportError:
    license_expression = None  # type: ignore[assignment]


CRYPTOGRAPHY_VERSION = Distribution.from_name("cryptography").version


class IntegrationTestCase(CommandLineTestCase):
    @classmethod
    def _create_pkg_name_columns(cls, table: PrettyTable) -> list[str]:
        index = DEFAULT_OUTPUT_FIELDS.index("Name")

        rows = copy.deepcopy(table.rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

    @classmethod
    def _create_license_columns(cls, table: PrettyTable, output_fields: list[str]) -> list[str]:
        index = output_fields.index("License")

        rows = copy.deepcopy(table.rows)
        pkg_name_columns = []
        for row in rows:
            pkg_name_columns.append(row[index])

        return pkg_name_columns

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
        self.assertEqual(output_fields, list(DEFAULT_OUTPUT_FIELDS) + ["License"])
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

        for license_name in ("BSD-3-Clause", "MIT", "Apache 2.0"):
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
        pkg_names = list(map(normalize_package_name, pkg_name_columns))
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
        pkg_name = "pycodestyle"
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

    def test_fail_on_partial_match(self) -> None:
        licenses = ("MIT",)
        allow_only_args = [
            "--partial-match",
            f"--fail-on={';'.join(licenses)}",
        ]

        with mock.patch("sys.exit"), CaptureOutput() as captured:
            args = create_parser().parse_args(allow_only_args)
            create_licenses_table(args)

        self.assertEqual("", captured.stdout)
        self.assertIn("fail-on license MIT License was found for package", captured.stderr)

    def test_allow_only(self) -> None:
        licenses = (
            "Bsd License",
            "Apache Software License",
            "Mozilla Public License 2.0 (MPL 2.0)",
            "Python Software Foundation License",
            "Public Domain",
            "GNU General Public License (GPL)",
            "GNU Library or Lesser General Public License (LGPL)",
        )
        allow_only_args = [f"--allow-only={';'.join(licenses)}"]

        with mock.patch("sys.exit"), CaptureOutput() as captured:
            args = create_parser().parse_args(allow_only_args)
            create_licenses_table(args)

        self.assertEqual("", captured.stdout)
        self.assertIn("license MIT License not in allow-only licenses was found for package", captured.stderr)

    def test_allow_only_collect_all_failures(self) -> None:
        licenses = (
            "Apache Software License",
            "Mozilla Public License 2.0 (MPL 2.0)",
            "Python Software Foundation License",
            "Public Domain",
            "GNU General Public License (GPL)",
            "GNU Library or Lesser General Public License (LGPL)",
        )
        allow_only_args = [
            f"--allow-only={';'.join(licenses)}",
            "--collect-all-failures",
        ]

        with mock.patch("sys.exit"), CaptureOutput() as captured:
            args = create_parser().parse_args(allow_only_args)
            create_licenses_table(args)

        self.assertIn("license MIT License not in allow-only licenses was found for package", captured.stderr)
        self.assertIn("license BSD License not in allow-only licenses was found for package", captured.stderr)

    def test_allow_only_partial(self) -> None:
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
            f"--allow-only={';'.join(licenses)}",
        ]

        with mock.patch("sys.exit"), CaptureOutput() as captured:
            args = create_parser().parse_args(allow_only_args)
            create_licenses_table(args)

        self.assertEqual("", captured.stdout)
        self.assertIn("license MIT License not in allow-only licenses was found for package", captured.stderr)

    def test_different_python(self) -> None:
        class TempEnvBuild(venv.EnvBuilder):
            def post_setup(self, context: SimpleNamespace) -> None:
                self.context = context

        with TemporaryDirectory() as target_dir_path:
            venv_builder = TempEnvBuild(with_pip=True)
            venv_builder.create(str(target_dir_path))
            python_exec = venv_builder.context.env_exe
            python_arg = f"--python={python_exec}"
            args = create_parser().parse_args([python_arg, "-s", "-f=json"])
            pkgs = get_packages(args)
            package_names = sorted({p.name for p in pkgs})

        expected_packages = ["pip"]
        if sys.version_info < (3, 12, 0):
            expected_packages.append("setuptools")
        assert package_names == expected_packages

    def test_fail_on(self) -> None:
        licenses = ("MIT license",)
        allow_only_args = [f"--fail-on={';'.join(licenses)}"]

        with mock.patch("sys.exit"), CaptureOutput() as captured:
            args = create_parser().parse_args(allow_only_args)
            create_licenses_table(args)

        self.assertEqual("", captured.stdout)
        self.assertIn("fail-on license MIT License was found for package", captured.stderr)

    def test_fail_on_collect_all_failures(self) -> None:
        licenses = ("MIT License", "BSD License")
        fail_on_args = [
            f"--fail-on={';'.join(licenses)}",
            "--collect-all-failures",
        ]

        with mock.patch("sys.exit"), CaptureOutput() as captured:
            args = create_parser().parse_args(fail_on_args)
            create_licenses_table(args)

        self.assertIn("fail-on license MIT License was found for package", captured.stderr)
        self.assertIn("fail-on license BSD License was found for package", captured.stderr)

    def test_spdx_operator_or_succeeds_if_either_license_is_allowed(self) -> None:
        # cryptography has an "Apache-2.0 OR BSD-3-Clause" license SPDX expression
        for expression in ["Apache-2.0", "BSD-3-Clause"]:
            spdx_args_success = [
                f"--allow-only={expression}",
                "--packages=cryptography",
            ]

            with mock.patch("sys.exit"), CaptureOutput() as captured:
                args = create_parser().parse_args(spdx_args_success)
                create_licenses_table(args)

            if license_expression is not None:
                self.assertEqual("", captured.stderr)
            else:
                self.assertEqual(
                    f"license Apache-2.0 OR BSD-3-Clause not in allow-only licenses was found for package cryptography:{CRYPTOGRAPHY_VERSION}\n",
                    captured.stderr,
                )

    def test_spdx_operator_or_fails_if_either_license_is_not_allowed(self) -> None:
        # cryptography has an "Apache-2.0 OR BSD-3-Clause" license SPDX expression
        for expression in ["Apache-2.0", "BSD-3-Clause"]:
            spdx_args_failure = [
                f"--fail-on={expression}",
                "--packages=cryptography",
            ]
            with mock.patch("sys.exit"), CaptureOutput() as captured:
                args = create_parser().parse_args(spdx_args_failure)
                create_licenses_table(args)

            if license_expression is None:
                self.assertEqual("", captured.stderr)
            else:
                self.assertEqual(f"fail-on license {expression} was found for package cryptography:{CRYPTOGRAPHY_VERSION}\n", captured.stderr)

    def test_file_handling(self) -> None:
        package = PackageInfo(
            name="test-package",
            version="1.0",
            distribution=PathDistribution.from_name("pip-licenses-lib"),
            licenses=[
                ("/django/contrib/admin/static/admin/css/vendor/select2/LICENSE-SELECT2.md", "This is the SELECT2 license text."),
                ("/django-5.2.6.dist-info/licenses/LICENSE", "This is the primary license text."),
                ("/django-5.2.6.dist-info/licenses/LICENSE.python", "This is the license for upstream Python."),
            ],
            notices=[
                ("/django-5.2.6.dist-info/licenses/NOTICE1", "This is the first notice file."),
                ("/django-5.2.6.dist-info/licenses/NOTICE2", "This is the second notice file."),
            ],
            others=[
                ("/django-5.2.6.dist-info/licenses/AUTHORS", "This is the AUTHORS file."),
                ("/django-5.2.6.dist-info/licenses/TESTING", "This is a dummy file for testing."),
            ],
        )

        with mock.patch("piplicenses.collector._get_packages", return_value=[package]):
            args = create_parser().parse_args(["--format=plain-vertical"])
            result = create_output_string(args)
            self.assertEqual("test-package\n1.0\n\n\n", result)

            args = create_parser().parse_args(["--format=plain-vertical", "--with-license-file", "--with-notice-file"])
            result = create_output_string(args)
            self.assertEqual(
                """test-package
1.0

/django/contrib/admin/static/admin/css/vendor/select2/LICENSE-SELECT2.md
This is the SELECT2 license text.
/django-5.2.6.dist-info/licenses/NOTICE1
This is the first notice file.

""",
                result,
            )

            args = create_parser().parse_args(["--format=plain-vertical", "--with-license-files", "--with-notice-files", "--with-other-files"])
            result = create_output_string(args)
            self.assertEqual(
                """test-package
1.0

/django/contrib/admin/static/admin/css/vendor/select2/LICENSE-SELECT2.md
This is the SELECT2 license text.
/django-5.2.6.dist-info/licenses/LICENSE
This is the primary license text.
/django-5.2.6.dist-info/licenses/LICENSE.python
This is the license for upstream Python.
/django-5.2.6.dist-info/licenses/NOTICE1
This is the first notice file.
/django-5.2.6.dist-info/licenses/NOTICE2
This is the second notice file.
/django-5.2.6.dist-info/licenses/AUTHORS
This is the AUTHORS file.
/django-5.2.6.dist-info/licenses/TESTING
This is a dummy file for testing.

""",
                result,
            )

            args = create_parser().parse_args(
                ["--format=plain-vertical", "--with-license-files", "--with-notice-files", "--with-other-files", "--no-license-path"]
            )
            result = create_output_string(args)
            self.assertEqual(
                """test-package
1.0

This is the SELECT2 license text.
This is the primary license text.
This is the license for upstream Python.
This is the first notice file.
This is the second notice file.
This is the AUTHORS file.
This is a dummy file for testing.

""",
                result,
            )

            args = create_parser().parse_args(["--format=json"])
            result = create_output_string(args)
            self.assertEqual([{"License": "", "Name": "test-package", "Version": "1.0"}], json.loads(result))

            args = create_parser().parse_args(["--format=json", "--with-license-file", "--with-notice-file"])
            result = create_output_string(args)
            self.assertEqual(
                [
                    {
                        "License": "",
                        "LicenseFile": "/django/contrib/admin/static/admin/css/vendor/select2/LICENSE-SELECT2.md",
                        "LicenseText": "This is the SELECT2 license text.",
                        "Name": "test-package",
                        "NoticeFile": "/django-5.2.6.dist-info/licenses/NOTICE1",
                        "NoticeText": "This is the first notice file.",
                        "Version": "1.0",
                    }
                ],
                json.loads(result),
            )

            args = create_parser().parse_args(["--format=json", "--with-license-files", "--with-notice-files", "--with-other-files"])
            result = create_output_string(args)
            self.assertEqual(
                [
                    {
                        "License": "",
                        "LicenseFiles": [
                            "/django/contrib/admin/static/admin/css/vendor/select2/LICENSE-SELECT2.md",
                            "/django-5.2.6.dist-info/licenses/LICENSE",
                            "/django-5.2.6.dist-info/licenses/LICENSE.python",
                        ],
                        "LicenseTexts": ["This is the SELECT2 license text.", "This is the primary license text.", "This is the license for upstream Python."],
                        "Name": "test-package",
                        "NoticeFiles": ["/django-5.2.6.dist-info/licenses/NOTICE1", "/django-5.2.6.dist-info/licenses/NOTICE2"],
                        "NoticeTexts": ["This is the first notice file.", "This is the second notice file."],
                        "OtherFiles": ["/django-5.2.6.dist-info/licenses/AUTHORS", "/django-5.2.6.dist-info/licenses/TESTING"],
                        "OtherTexts": ["This is the AUTHORS file.", "This is a dummy file for testing."],
                        "Version": "1.0",
                    }
                ],
                json.loads(result),
            )
