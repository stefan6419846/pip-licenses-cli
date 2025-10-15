# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

import warnings
from unittest import TestCase

from piplicenses.errors import PipLicensesWarning
from piplicenses.spdx import _get_spdx_parser

try:
    import license_expression
except ImportError:
    license_expression = None  # type: ignore[assignment]


class SpdxParserTestCase(TestCase):
    def test_has_license_expression_package(self):
        if license_expression is None:
            raise self.skipTest("Requires license-expression package.")

        for test_id, expression, expected, should_warn in [
            (
                "SPDX WITH",
                "GPL-2.0-or-later WITH Bison-exception-2.2",
                {"GPL-2.0-or-later WITH Bison-exception-2.2"},
                True,
            ),
            ("SPDX AND", "Apache-2.0 AND BSD-3-Clause", {"Apache-2.0 AND BSD-3-Clause"}, True),
            ("SPDX OR", "Apache-2.0 OR BSD-3-Clause", {"Apache-2.0", "BSD-3-Clause"}, False),
            ("Invalid SPDX", "Hello World", {"Hello World"}, False),
            ("Empty", "", {""}, False),
        ]:
            with self.subTest(test_id=test_id, expression=expression):
                if should_warn:
                    with warnings.catch_warnings(record=True) as caught_warnings:
                        warnings.simplefilter("always")
                        self.assertEqual(expected, _get_spdx_parser()(expression))
                        self.assertEqual(1, len(caught_warnings), caught_warnings)
                        self.assertEqual(PipLicensesWarning, caught_warnings[0].category)
                else:
                    self.assertEqual(expected, _get_spdx_parser()(expression))

    def test_does_not_have_license_expression_package(self):
        if license_expression is not None:
            raise self.skipTest("Does not work with license-expression package.")

        for (
            test_id,
            expression,
        ) in [
            ("SPDX WITH", "GPL-2.0-or-later WITH Bison-exception-2.2"),
            ("SPDX AND", "Apache-2.0 AND BSD-3-Clause"),
            ("SPDX OR", "Apache-2.0 OR BSD-3-Clause"),
            ("Invalid SPDX", "Hello World"),
            ("Empty", ""),
        ]:
            with self.subTest(test_id=test_id, expression=expression):
                self.assertEqual({expression}, _get_spdx_parser()(expression))
