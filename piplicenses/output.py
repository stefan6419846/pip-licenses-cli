# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, cast

from piplicenses_lib import LICENSE_UNKNOWN
from prettytable import HRuleStyle, PrettyTable

from piplicenses.collector import get_packages
from piplicenses.constants import DEFAULT_OUTPUT_FIELDS, FIELDS_TO_METADATA_KEYS, SUMMARY_FIELD_NAMES

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

    from prettytable import RowType

    from piplicenses.cli import CustomNamespace


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


def create_summary_table(args: CustomNamespace) -> PrettyTable:
    counts = Counter("; ".join(sorted(pkg.license_names)) for pkg in get_packages(args))

    table = factory_styled_table_with_args(args, SUMMARY_FIELD_NAMES)
    for license_, count in counts.items():
        table.add_row([count, license_])
    return table


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

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        lines = [self.format_row(row) for row in rows]
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

        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        formatted_rows = self._format_rows(rows)

        lines: list[str] = []
        formatted_header = ",".join([f'"{esc_quotes(val)}"' for val in self._field_names])
        lines.append(formatted_header)
        lines.extend([",".join([f'"{esc_quotes(val)}"' for val in row]) for row in formatted_rows])
        return "\n".join(lines)


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
    from piplicenses.cli import FormatArg

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
