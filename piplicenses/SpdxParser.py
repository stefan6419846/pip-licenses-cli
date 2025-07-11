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

# import argparse
import codecs
import functools
import sys
import warnings

from .PipLicensesWarning import (
    PipLicensesWarning,
    PIP_LICENSE_CLI_WARN_MSG_SPDX_UNSUPPORTED_CLAUSE,
)

# from collections import Counter
# from dataclasses import asdict
# from enum import Enum, auto
# from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, Type, cast

from piplicenses_lib import (
    LICENSE_UNKNOWN,
    FromArg,
    NoValueEnum,
)
from prettytable import HRuleStyle, PrettyTable

from . import __pkgname__ as __pkgname__  # skipcq: PYL-C0414

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterator, Optional, Sequence

    from piplicenses_lib import PackageInfo
    from prettytable import RowType


open = open  # allow monkey patching

from .cli import CustomNamespace

# will need to create aliases for backwards compatibility. E.g.,
from .cli.OrderArg import OrderArg
from .cli.FormatArg import FormatArg

SYSTEM_PACKAGES = [
    __pkgname__,
    "pip",
    "pip-licenses-lib",
    "prettytable",
    "wcwidth",
    "setuptools",
    "wheel",
]
if sys.version_info < (3, 11):  # pragma: no cover
    SYSTEM_PACKAGES.append("tomli")


class SpdxParser(Protocol):
    def __call__(self, expression: str) -> set[str]:  # pragma: no cover
        pass


@functools.lru_cache(maxsize=1)
def _get_spdx_parser() -> SpdxParser:
    """
    Create an SPDX expression parser.

    If the extra "spdx" is not installed, then the parser just returns a set
    with the provided expression as the only element.
    """
    try:
        from license_expression import get_spdx_licensing

    except ImportError:

        def dummy_parser(expression: str) -> set[str]:
            return {expression}

        return dummy_parser

    SYSTEM_PACKAGES.append("license-expression")
    SYSTEM_PACKAGES.append("boolean-py")

    licensing = get_spdx_licensing()

    def parser(expression: str) -> set[str]:
        try:
            result = licensing.validate(expression)
        except Exception:
            # https://github.com/aboutcode-org/license-expression/issues/97
            return {expression}
        if result.errors:
            return {expression}
        parsed = licensing.parse(expression)
        if parsed is None:
            return {expression}
        parsed = parsed.simplify()
        parsed_str = str(parsed)
        if "AND" in parsed_str or "WITH" in parsed_str:
            warnings.warn(
                f"{PIP_LICENSE_CLI_WARN_MSG_SPDX_UNSUPPORTED_CLAUSE} The expression {parsed} is treated as the literal {expression!r}.",
                category=PipLicensesWarning,
                stacklevel=2,
            )
            return {expression}
        return {license_name for license_name in parsed.objects}

    return parser


def _parse_spdx(
    expression: str,
) -> set[str]:
    """Parse a license expression and return a set of licenses."""
    return _get_spdx_parser()(expression)
