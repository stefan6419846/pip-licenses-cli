# pip-licenses-cli
#
# MIT License
#
# Copyright (c) 2018 raimon
# Copyright (c) 2025 stefan6419846
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Type

from piplicenses_lib import (
    FromArg,
    NoValueEnum,
)

from .compatible_arg_parser import CompatibleArgumentParser
from .custom_help_formatter import CustomHelpFormatter
from .custom_namespace import CustomNamespace
from .format_arg import FormatArg
from .order_arg import OrderArg
from .select_action import (
    SelectAction,
    get_value_from_enum,
)

# Triggers F401 -- Unused -- kept for historical note
# from .custom_help_formatter import enum_key_to_value

# Triggers F401 -- Unused -- kept for historical note
# from .select_action import (
#     MAP_DEST_TO_ENUM,
#     value_to_enum_key,
# )


if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


# Package version imported for `--version` output
from .. import __version__ as __version__  # skipcq: PYL-C0414

__summary__ = "Dump the software license list of Python packages installed with pip."

open = open  # allow monkey patching


# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS = {
    "URL": "homepage",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "LicenseFile": "license_files",
    "LicenseText": "license_texts",
    "NoticeFile": "notice_files",
    "NoticeText": "notice_texts",
    "Description": "summary",
}


# toml [tool.pip-licenses] section name
# Not using __pkgname__ because we want to be backwards compatible
TOML_SECTION_NAME: str = "pip-licenses"


def choices_from_enum(enum_cls: Type[NoValueEnum]) -> list[str]:
    return [key.replace("_", "-").lower() for key in enum_cls.__members__.keys()]


def get_sortby(args: CustomNamespace) -> str:
    if args.summary and args.order == OrderArg.COUNT:
        return "Count"
    elif args.summary or args.order == OrderArg.LICENSE:
        return "License"
    elif args.order == OrderArg.NAME:
        return "Name"
    elif args.order == OrderArg.AUTHOR and args.with_authors:
        return "Author"
    elif args.order == OrderArg.MAINTAINER and args.with_maintainers:
        return "Maintainer"
    elif args.order == OrderArg.URL and args.with_urls:
        return "URL"

    return "Name"


def load_config_from_file(pyproject_path: str) -> dict:
    if Path(pyproject_path).exists():
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f).get("tool", {}).get(TOML_SECTION_NAME, {})
    return {}


def create_parser(
    pyproject_path: str = "pyproject.toml",
) -> CompatibleArgumentParser:
    parser = CompatibleArgumentParser(description=__summary__, formatter_class=CustomHelpFormatter)
    # Load any user defaults from pyproject.toml
    config_from_file = load_config_from_file(pyproject_path)
    # Define argument groups
    common_options = parser.add_argument_group("Common options")
    format_options = parser.add_argument_group("Format options")
    verify_options = parser.add_argument_group("Verify options")
    # Version flag
    parser.add_argument("-v", "--version", action="version", version="%(prog)s " + __version__)
    # Common options
    common_options.add_argument(
        "--python",
        type=str,
        default=config_from_file.get("python", sys.executable),
        metavar="PYTHON_EXEC",
        help=(
            "R| path to python executable to search distributions from\n"
            "Package will be searched in the selected python's sys.path\n"
            "By default, will search packages for current env executable\n"
            "(default: sys.executable)"
        ),
    )
    common_options.add_argument(
        "--from",
        dest="from_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(FromArg, config_from_file.get("from", "mixed")),
        metavar="SOURCE",
        choices=choices_from_enum(FromArg),
        help='R|where to find license information\n"meta", "classifier, "mixed", "all"\n(default: %(default)s)',
    )
    common_options.add_argument(
        "-o",
        "--order",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(OrderArg, config_from_file.get("order", "name")),
        metavar="COL",
        choices=choices_from_enum(OrderArg),
        help='R|order by column\n"name", "license", "author", "url"\n(default: %(default)s)',
    )
    common_options.add_argument(
        "-f",
        "--format",
        dest="format_",
        action=SelectAction,
        type=str,
        default=get_value_from_enum(FormatArg, config_from_file.get("format", "plain")),
        metavar="STYLE",
        choices=choices_from_enum(FormatArg),
        help=(
            "R|dump as set format style\n"
            '"plain", "plain-vertical" "markdown", "rst", \n'
            '"confluence", "html", "json", \n'
            '"json-license-finder",  "csv"\n'
            "(default: %(default)s)"
        ),
    )
    common_options.add_argument(
        "--summary",
        action="store_true",
        default=config_from_file.get("summary", False),
        help="dump summary of each license",
    )
    common_options.add_argument(
        "--output-file",
        action="store",
        default=config_from_file.get("output-file"),
        type=str,
        help="save license list to file",
    )
    common_options.add_argument(
        "-i",
        "--ignore-packages",
        action="store",
        type=str,
        nargs="+",
        metavar="PKG",
        default=config_from_file.get("ignore-packages", []),
        help="ignore package name in dumped list",
    )
    common_options.add_argument(
        "-p",
        "--packages",
        action="store",
        type=str,
        nargs="+",
        metavar="PKG",
        default=config_from_file.get("packages", []),
        help="only include selected packages in output",
    )
    # Format options
    format_options.add_argument(
        "-s",
        "--with-system",
        action="store_true",
        default=config_from_file.get("with-system", False),
        help="dump with system packages",
    )
    format_options.add_argument(
        "-a",
        "--with-authors",
        action="store_true",
        default=config_from_file.get("with-authors", False),
        help="dump with package authors",
    )
    format_options.add_argument(
        "--with-maintainers",
        action="store_true",
        default=config_from_file.get("with-maintainers", False),
        help="dump with package maintainers",
    )
    format_options.add_argument(
        "-u",
        "--with-urls",
        action="store_true",
        default=config_from_file.get("with-urls", False),
        help="dump with package urls",
    )
    format_options.add_argument(
        "-d",
        "--with-description",
        action="store_true",
        default=config_from_file.get("with-description", False),
        help="dump with short package description",
    )
    format_options.add_argument(
        "-nv",
        "--no-version",
        action="store_true",
        default=config_from_file.get("no-version", False),
        help="dump without package version",
    )
    format_options.add_argument(
        "-l",
        "--with-license-file",
        action="store_true",
        default=config_from_file.get("with-license-file", False),
        help="dump with location of license file and contents, most useful with JSON output",
    )
    format_options.add_argument(
        "--no-license-path",
        action="store_true",
        default=config_from_file.get("no-license-path", False),
        help="I|when specified together with option -l, suppress location of license file output",
    )
    format_options.add_argument(
        "--with-notice-file",
        action="store_true",
        default=config_from_file.get("with-notice-file", False),
        help="I|when specified together with option -l, dump with location of license file and contents",
    )
    format_options.add_argument(
        "--filter-strings",
        action="store_true",
        default=config_from_file.get("filter-strings", False),
        help="filter input according to code page",
    )
    format_options.add_argument(
        "--filter-code-page",
        action="store",
        type=str,
        default=config_from_file.get("filter-code-page", "latin1"),
        metavar="CODE",
        help="I|specify code page for filtering (default: %(default)s)",
    )
    # Verify options
    verify_options.add_argument(
        "--fail-on",
        action="store",
        type=str,
        default=config_from_file.get("fail-on", None),
        help="fail (exit with code 1) on the first occurrence of the licenses of the semicolon-separated list",
    )
    verify_options.add_argument(
        "--allow-only",
        action="store",
        type=str,
        default=config_from_file.get("allow-only", None),
        help="fail (exit with code 1) on the first occurrence of the licenses not in the semicolon-separated list",
    )
    verify_options.add_argument(
        "--partial-match",
        action="store_true",
        default=config_from_file.get("partial-match", False),
        help="enables partial matching for --allow-only/--fail-on",
    )
    verify_options.add_argument(
        "--collect-all-failures",
        action="store_true",
        default=config_from_file.get("collect-all-failures", False),
        help="collect all license failures and report them after processing all packages",
    )
    # Finally return the parser
    return parser
