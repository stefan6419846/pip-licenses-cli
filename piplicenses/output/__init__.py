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

from .colors import output_colored  # noqa: F401

import sys
from collections import Counter
from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from piplicenses_lib import (
    LICENSE_UNKNOWN,
    FromArg,
)
from piplicenses_lib import get_packages as _get_packages
from piplicenses_lib import (
    normalize_package_name,
)
from prettytable import HRuleStyle, PrettyTable

from ..cli import get_sortby
from ..cli.custom_namespace import CustomNamespace
from ..cli.format_arg import FormatArg
from ..collection import (
    case_insensitive_partial_match_set_diff,
    case_insensitive_partial_match_set_intersect,
    case_insensitive_set_diff,
    case_insensitive_set_intersect,
)
from ..spdx import (
    SYSTEM_PACKAGES,
    _parse_spdx,
)

# Triggers F401 -- Unused -- kept for historical note
# see https://docs.python.org/3/library/tomllib.html
if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib  # noqa: F401
else:  # pragma: no cover
    import tomli as tomllib  # noqa: F401


if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterator, Sequence

    from piplicenses_lib import PackageInfo

from .csv import CSVPrettyTable
from .json import (
    JsonLicenseFinderTable,
    JsonPrettyTable,
)
from .plain import PlainVerticalTable

open = open  # allow monkey patching


FIELD_NAMES = (
    "Name",
    "Version",
    "License",
    "LicenseFile",
    "LicenseText",
    "NoticeFile",
    "NoticeText",
    "Author",
    "Maintainer",
    "Description",
    "URL",
)


SUMMARY_FIELD_NAMES = (
    "Count",
    "License",
)


DEFAULT_OUTPUT_FIELDS = (
    "Name",
    "Version",
)


SUMMARY_OUTPUT_FIELDS = (
    "Count",
    "License",
)

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


def factory_styled_table_with_args(
    args: CustomNamespace,
    output_fields: Sequence[str] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = PrettyTable()
    table.field_names = output_fields  # type: ignore[assignment]
    table.align = "l"  # type: ignore[assignment]
    table.border = args.format_ in {
        FormatArg.MARKDOWN,
        FormatArg.RST,
        FormatArg.CONFLUENCE,
        FormatArg.JSON,
    }
    table.header = True

    if args.format_ == FormatArg.MARKDOWN:
        table.junction_char = "|"
        table.hrules = HRuleStyle.HEADER
    elif args.format_ == FormatArg.RST:
        table.junction_char = "+"
        table.hrules = HRuleStyle.ALL
    elif args.format_ == FormatArg.CONFLUENCE:
        table.junction_char = "|"
        table.hrules = HRuleStyle.NONE
    elif args.format_ == FormatArg.JSON:
        table = JsonPrettyTable(table.field_names)
    elif args.format_ == FormatArg.JSON_LICENSE_FINDER:
        table = JsonLicenseFinderTable(table.field_names)
    elif args.format_ == FormatArg.CSV:
        table = CSVPrettyTable(table.field_names)
    elif args.format_ == FormatArg.PLAIN_VERTICAL:
        table = PlainVerticalTable(table.field_names)

    return table


def create_summary_table(args: CustomNamespace) -> PrettyTable:
    counts = Counter("; ".join(sorted(pkg.license_names)) for pkg in get_packages(args))

    table = factory_styled_table_with_args(args, SUMMARY_FIELD_NAMES)
    for license, count in counts.items():
        table.add_row([count, license])
    return table


def get_packages(
    args: CustomNamespace,
) -> Iterator[PackageInfo]:
    ignore_pkgs_as_normalize = [normalize_package_name(pkg) for pkg in args.ignore_packages]
    pkgs_as_normalize = [normalize_package_name(pkg) for pkg in args.packages]

    fail_on_licenses = set()
    if args.fail_on:
        fail_on_licenses = set(map(str.strip, args.fail_on.split(";")))

    allow_only_licenses = set()
    if args.allow_only:
        allow_only_licenses = set(map(str.strip, args.allow_only.split(";")))

    include_files = args.with_license_file or args.with_notice_file
    failures = []
    for pkg_info in _get_packages(
        from_source=args.from_,
        python_path=args.python,
        include_files=include_files,
        normalize_names=False,
    ):
        pkg_name = normalize_package_name(pkg_info.name)
        pkg_name_and_version = pkg_name + ":" + pkg_info.version

        if pkg_name.lower() in ignore_pkgs_as_normalize or pkg_name_and_version.lower() in ignore_pkgs_as_normalize:
            continue

        if pkgs_as_normalize and pkg_name.lower() not in pkgs_as_normalize:
            continue

        if not args.with_system and pkg_name in SYSTEM_PACKAGES:
            continue

        if args.filter_strings:

            def filter_string(item: str) -> str:
                return item.encode(args.filter_code_page, errors="ignore").decode(args.filter_code_page)

            for key, value in asdict(pkg_info).items():
                if key == "distribution":
                    continue

                def _handle(_value):
                    if isinstance(_value, list):
                        return list(map(_handle, _value))
                    if isinstance(_value, set):
                        return set(map(_handle, _value))
                    if isinstance(_value, tuple):
                        return tuple(map(_handle, _value))
                    return filter_string(cast(str, _value))

                setattr(pkg_info, key, _handle(value))

        parsed_license_names: set[str] = set()
        for license_expr in pkg_info.license_names:
            parsed_license_names |= _parse_spdx(license_expr)

        fail_this_pkg = False
        fail_message = ""
        if fail_on_licenses:
            if not args.partial_match:
                failed_licenses = case_insensitive_set_intersect(parsed_license_names, fail_on_licenses)
            else:
                failed_licenses = case_insensitive_partial_match_set_intersect(parsed_license_names, fail_on_licenses)
            if failed_licenses:
                fail_this_pkg = True
                fail_message = "fail-on license {} was found for package {}:{}\n".format(
                    "; ".join(sorted(failed_licenses)),
                    pkg_info.name,
                    pkg_info.version,
                )
        if allow_only_licenses:
            if not args.partial_match:
                uncommon_licenses = case_insensitive_set_diff(parsed_license_names, allow_only_licenses)
            else:
                uncommon_licenses = case_insensitive_partial_match_set_diff(parsed_license_names, allow_only_licenses)
            if len(uncommon_licenses) == len(parsed_license_names):
                fail_this_pkg = True
                fail_message = "license {} not in allow-only licenses was found for package {}:{}\n".format(
                    "; ".join(sorted(uncommon_licenses)),
                    pkg_info.name,
                    pkg_info.version,
                )
        if fail_this_pkg:
            if args.collect_all_failures:
                failures.append(fail_message)
            else:
                sys.stderr.write(fail_message)
                sys.exit(1)

        yield pkg_info

    if args.collect_all_failures and failures:
        for msg in failures:
            sys.stderr.write(msg)
        sys.exit(1)


def create_licenses_table(
    args: CustomNamespace,
    output_fields: Sequence[str] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = factory_styled_table_with_args(args, output_fields)

    for pkg in get_packages(args):
        row = []
        for field in output_fields:
            if field == "License":
                license_set = pkg.license_names
                license_str = "; ".join(sorted(license_set))
                row.append(license_str)
            elif field == "License-Classifier":
                row.append("; ".join(sorted(pkg.license_classifiers)) or LICENSE_UNKNOWN)
            elif hasattr(pkg, field.lower()):
                row.append(cast(str, getattr(pkg, field.lower())))
            else:
                value = getattr(pkg, FIELDS_TO_METADATA_KEYS[field])
                if field in {
                    "LicenseFile",
                    "LicenseText",
                    "NoticeFile",
                    "NoticeText",
                }:
                    row.append(cast(str, next(value, LICENSE_UNKNOWN)))
                else:
                    row.append(cast(str, value))
        table.add_row(row)

    return table


def get_output_fields(args: CustomNamespace) -> list[str]:
    if args.summary:
        return list(SUMMARY_OUTPUT_FIELDS)

    output_fields: list = list(DEFAULT_OUTPUT_FIELDS)

    if args.from_ == FromArg.ALL:
        output_fields.append("License-Metadata")
        output_fields.append("License-Classifier")
    else:
        output_fields.append("License")

    if args.with_authors:
        output_fields.append("Author")

    if args.with_maintainers:
        output_fields.append("Maintainer")

    if args.with_urls:
        output_fields.append("URL")

    if args.with_description:
        output_fields.append("Description")

    if args.no_version:
        output_fields.remove("Version")

    if args.with_license_file:
        if not args.no_license_path:
            output_fields.append("LicenseFile")

        output_fields.append("LicenseText")

        if args.with_notice_file:
            output_fields.append("NoticeText")
            if not args.no_license_path:
                output_fields.append("NoticeFile")

    return output_fields


def create_output_string(args: CustomNamespace) -> str:
    output_fields: list = get_output_fields(args)

    if args.summary:
        table = create_summary_table(args)
    else:
        table = create_licenses_table(args, output_fields)

    sortby = get_sortby(args)

    if args.format_ == FormatArg.HTML:
        html = table.get_html_string(fields=output_fields, sortby=sortby)
        return html.encode("ascii", errors="xmlcharrefreplace").decode("ascii")
    else:
        return table.get_string(fields=output_fields, sortby=sortby)
