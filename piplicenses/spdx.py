# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

import functools
import warnings
from typing import Protocol

from piplicenses.constants import SYSTEM_PACKAGES
from piplicenses.errors import PipLicensesWarning


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
                f"SPDX expressions with 'AND' or 'WITH' are currently not supported. The expression {parsed} is treated as the literal {expression!r}.",
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
