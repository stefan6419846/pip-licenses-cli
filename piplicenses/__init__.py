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

# Triggers F401 -- Unused -- kept for historical note
# import argparse
# import codecs
# import functools
# import warnings

__pkgname__ = "pip-licenses-cli"
__version__ = "1.4.0"

# Triggers F401 -- Unused -- kept for historical note
# from piplicenses_lib import (
#     LICENSE_UNKNOWN,
#     NoValueEnum,
# )
from piplicenses_lib import FromArg  # noqa: F401

from .constants import TOML_SECTION_NAME  # noqa: F401
from .constants import FIELDS_TO_METADATA_KEYS  # noqa: F401
from .constants import DEFAULT_OUTPUT_FIELDS  # noqa: F401
from .constants import SYSTEM_PACKAGES  # noqa: F401

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .cli import CustomNamespace  # noqa: F401
from .cli import get_sortby  # noqa: F401
from .cli import load_config_from_file  # noqa: F401
from .cli import create_parser

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .cli import CompatibleArgumentParser  # noqa: F401

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .cli import CustomHelpFormatter  # noqa: F401
from .cli import enum_key_to_value  # noqa: F401
from .cli import FormatArg  # noqa: F401

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .cli import OrderArg  # noqa: F401

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .cli import SelectAction  # noqa: F401
from .cli import value_to_enum_key  # noqa: F401

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
# from .spdx import SYSTEM_PACKAGES  # noqa: F401
from .spdx import _get_spdx_parser  # noqa: F401

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .output import create_licenses_table  # noqa: F401
from .output import factory_styled_table_with_args  # noqa: F401
from .output import get_output_fields  # noqa: F401
from .output import create_output_string

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .errors import output_colored  # noqa: F401
from .errors import PipLicensesWarning  # noqa: F401
from .errors import create_warn_string

# Triggers F401 -- Unused -- kept for historical testing backwards compatibility
from .collection import get_packages  # noqa: F401
from .collection import case_insensitive_partial_match_set_diff  # noqa: F401
from .collection import case_insensitive_partial_match_set_intersect  # noqa: F401
from .collection import case_insensitive_set_diff  # noqa: F401
from .collection import case_insensitive_set_intersect  # noqa: F401

# Triggers F401 -- Unused -- kept for historical note
# from .spdx import (
#     SpdxParser,
#     _parse_spdx,
# )

# Triggers F401 -- Unused -- kept for historical note
# from prettytable import HRuleStyle, PrettyTable

# Triggers F401 -- Unused -- kept for historical note
# from .cli import (
#     load_config_from_file,
#     get_sortby,
#     TOML_SECTION_NAME,
# )

# Triggers F401 -- Unused -- kept for historical note
# from .output import (
#     SUMMARY_FIELD_NAMES,
#     FIELD_NAMES,
#     DEFAULT_OUTPUT_FIELDS,
#     SUMMARY_OUTPUT_FIELDS,
#     get_packages,
#     create_summary_table,
#     get_output_fields,
#     factory_styled_table_with_args,
#     create_licenses_table,
#     create_output_string,
# )

# Triggers F401 -- Unused -- kept for historical note
# see https://docs.python.org/3/library/tomllib.html
if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib  # noqa: F401
else:  # pragma: no cover
    import tomli as tomllib  # noqa: F401

# Triggers F401 -- Unused -- kept for historical note
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:  # pragma: no cover
#     from piplicenses_lib import PackageInfo  # noqa: F401
#     from prettytable import RowType  # noqa: F401


open = open  # allow monkey patching


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
    warn_string = create_warn_string(args)
    if warn_string:
        print(warn_string, file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    main()
