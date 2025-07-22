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

# ANSI Color Codes
from .constants import (
    SUMMARY_FIELD_NAMES,
    DEFAULT_OUTPUT_FIELDS,
    SUMMARY_OUTPUT_FIELDS,
    FIELDS_TO_METADATA_KEYS,
)

import sys
from collections import Counter
from typing import (
    TYPE_CHECKING,
    cast,
)
from piplicenses_lib import (
    LICENSE_UNKNOWN,
    FromArg,
)
from prettytable import HRuleStyle, PrettyTable

from .cli import get_sortby
from .cli import CustomNamespace
from .cli import FormatArg
from .collection import (
    get_packages,
)

# Triggers F401 -- Unused -- kept for historical note
# see https://docs.python.org/3/library/tomllib.html
if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib  # noqa: F401
else:  # pragma: no cover
    import tomli as tomllib  # noqa: F401


if TYPE_CHECKING:  # pragma: no cover
    from typing import Sequence
    from prettytable import RowType


open = open  # allow monkey patching


class CSVPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to CSV"""

    def get_string(self, **kwargs: str | list[str]) -> str:

        def esc_quotes(val: bytes | str) -> str:
            """
            Meta-escaping double quotes
            https://tools.ietf.org/html/rfc4180
            """
            try:
                return cast(str, val).replace('"', '""')
            except UnicodeDecodeError:  # pragma: no cover
                return cast(bytes, val).decode("utf-8").replace('"', '""')
            except UnicodeEncodeError:  # pragma: no cover
                return str(cast(str, val).encode("unicode_escape").replace('"', '""'))  # type: ignore[arg-type]

        # Retrieve formatting options (fields, limits, header flag, etc.)
        options = self._get_options(kwargs)
        # Build rows based on options.
        rows = self._get_rows(options)
        # Format rows via PrettyTable's own formatting logic.
        formatted_rows = self._format_rows(rows)
        lines: list[str] = []
        # Create CSV header line, with each field name escaped and quoted.
        formatted_header = ",".join([f'"{esc_quotes(val)}"' for val in self._field_names])
        lines.append(formatted_header)
        # Create CSV data lines.
        lines.extend([",".join([f'"{esc_quotes(val)}"' for val in row]) for row in formatted_rows])
        # Join all lines with newline separators.
        return "\n".join(lines)


class JsonPrettyTable(PrettyTable):
    """PrettyTable-like class exporting to JSON"""

    def format_row(self, row: RowType) -> dict[str, str | list[str]]:
        resrow: dict[str, str | list[str]] = {}
        for field, value in zip(self._field_names, row):
            resrow[field] = value

        return resrow

    def get_string(self, **kwargs: str | list[str]) -> str:
        # import included here in order to limit dependencies
        # if not interested in JSON output,
        # then the dependency is not required
        import json

        # Fetch formatting options (e.g., selected fields, row slice)
        options = self._get_options(kwargs)
        # Retrieve rows based on options
        rows = self._get_rows(options)
        # Convert rows to list of dicts
        lines = [self.format_row(row) for row in rows]
        # Serialize to JSON with indentation and sorted keys
        return json.dumps(lines, indent=2, sort_keys=True)


class JsonLicenseFinderTable(JsonPrettyTable):

    def format_row(self, row: RowType) -> dict[str, str | list[str]]:
        resrow: dict[str, str | list[str]] = {}
        for field, value in zip(self._field_names, row):
            if field == "Name":
                resrow["name"] = value
            if field == "Version":
                resrow["version"] = value
            if field == "License":
                resrow["licenses"] = [value]
        return resrow

    def get_string(self, **kwargs: str | list[str]) -> str:
        # import included here in order to limit dependencies
        # if not interested in JSON output,
        # then the dependency is not required
        import json

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        lines = [self.format_row(row) for row in rows]
        return json.dumps(lines, sort_keys=True)


class PlainVerticalTable(PrettyTable):
    """PrettyTable for outputting to a simple non-column based style.

    When used with --with-license-file, this style is similar to the default
    style generated from Angular CLI's --extractLicenses flag.
    """

    def get_string(self, **kwargs: str | list[str]) -> str:
        options = self._get_options(kwargs)
        rows = self._get_rows(options)

        output = ""
        for row in rows:
            for v in row:
                output += "{}\n".format(v)
            output += "\n"

        return output


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
