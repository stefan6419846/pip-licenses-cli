# pip-licenses-cli
#
# MIT License
#
# Copyright (c) 2018 raimon
# Copyright (c) 2025 stefan6419846
# Copyright (c) 2025 reactive-firewall
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
import warnings
from functools import lru_cache
from typing import Protocol

from . import __pkgname__ as __pkgname__  # skipcq: PYL-C0414

# from rest of project
from .errors import (
    PIP_LICENSE_CLI_WARN_MSG_SPDX_UNSUPPORTED_CLAUSE,
    PipLicensesWarning,
)

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


@lru_cache(maxsize=1)
def _get_spdx_parser() -> SpdxParser:
    """
    Create an SPDX expression parser.

    If the extra "spdx" is not installed, then the parser just returns a set
    with the provided expression as the only element.
    """
    try:
        from license_expression import get_spdx_licensing
    except ImportError:
        # Fallback: return the raw expression in a set
        def dummy_parser(expression: str) -> set[str]:
            return {expression}

        return dummy_parser

    # Real parser is available: record the dependency
    SYSTEM_PACKAGES.append("license-expression")
    SYSTEM_PACKAGES.append("boolean-py")

    licensing = get_spdx_licensing()

    def parser(expression: str) -> set[str]:
        try:
            result = licensing.validate(expression)
        except Exception:
            # https://github.com/aboutcode-org/license-expression/issues/97
            # On unexpected internal errors, treat as raw
            return {expression}
        if result.errors:
            # Invalid expression: treat as raw
            return {expression}
        parsed = licensing.parse(expression)
        if parsed is None:
            # Nothing parsed: treat as raw
            return {expression}
        parsed = parsed.simplify()
        parsed_str = str(parsed)
        if "AND" in parsed_str or "WITH" in parsed_str:
            # We do not support complex clauses: warn and treat literally
            warnings.warn(
                f"{PIP_LICENSE_CLI_WARN_MSG_SPDX_UNSUPPORTED_CLAUSE} " f"The expression {parsed} is treated as the literal {expression!r}.",
                category=PipLicensesWarning,
                stacklevel=2,
            )
            return {expression}
        # Return the set of objects (license identifiers) from the parsed expression
        return set(parsed.objects)

    return parser


def _parse_spdx(
    expression: str,
) -> set[str]:
    """Parse a license expression and return a set of licenses."""
    return _get_spdx_parser()(expression)
