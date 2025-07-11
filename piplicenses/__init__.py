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

import argparse
import codecs
import functools
import sys

# import warnings


__pkgname__ = "pip-licenses-cli"
__version__ = "1.4.0"

# Unused but here for backwards compatibility
from .setOps import (
    case_insensitive_set_diff,
    case_insensitive_set_intersect,
    case_insensitive_partial_match_set_intersect,
    case_insensitive_partial_match_set_diff,
)

from . import PipLicensesWarning
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, Type, cast

from piplicenses_lib import (
    LICENSE_UNKNOWN,
    FromArg,
    NoValueEnum,
)
from prettytable import HRuleStyle, PrettyTable

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterator, Optional, Sequence

    from piplicenses_lib import PackageInfo
    from prettytable import RowType


from .SpdxParser import (
    SpdxParser,
    SYSTEM_PACKAGES,
    _parse_spdx,
    _get_spdx_parser,
)

open = open  # allow monkey patching

from .cli import CustomNamespace

# will need to create aliases for backwards compatibility. E.g.,
from .cli.OrderArg import OrderArg
from .cli.FormatArg import FormatArg
from .cli.CustomHelpFormatter import (
    CustomHelpFormatter,
    enum_key_to_value,
)
from .cli.SelectAction import SelectAction as SelectAction  # skipcq: PYL-C0414
from .cli.CompatibleArgumentParser import CompatibleArgumentParser as CompatibleArgumentParser  # skipcq: PYL-C0414
from .cli import (
    load_config_from_file,
    create_parser,
    get_sortby,
    TOML_SECTION_NAME,
    create_parser,
    value_to_enum_key,
    enum_key_to_value,
)

from .output import (
    SUMMARY_FIELD_NAMES,
    FIELD_NAMES,
    DEFAULT_OUTPUT_FIELDS,
    SUMMARY_OUTPUT_FIELDS,
    get_packages,
    create_output_string,
    create_summary_table,
    get_output_fields,
    create_licenses_table,
    factory_styled_table_with_args,
)

# for testing 1:1 compatibility:
from .colors import output_colored
from .PipLicensesWarning import (
    PipLicensesWarning,
    create_warn_string,
)
from .output import create_licenses_table


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


def save_if_needs(output_file: None | str, output_string: str) -> None:
    """
    Save to path given by args
    """
    if output_file is None:
        return

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_string)
            if not output_string.endswith("\n"):
                # Always end output files with a new line
                f.write("\n")

        sys.stdout.write("created path: " + output_file + "\n")
        sys.exit(0)
    except IOError:
        sys.stderr.write("check path: --output-file\n")
        sys.exit(1)


def main() -> None:  # pragma: no cover
    parser = create_parser()
    args = parser.parse_args()

    output_string = create_output_string(args)

    output_file = args.output_file
    save_if_needs(output_file, output_string)

    print(output_string)
    warn_string = PipLicensesWarning.create_warn_string(args)
    if warn_string:
        print(warn_string, file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    main()
