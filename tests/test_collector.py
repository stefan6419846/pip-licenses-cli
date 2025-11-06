# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

from unittest import TestCase

from piplicenses.cli import CustomNamespace
from piplicenses.collector import (
    _should_include_files,
    case_insensitive_partial_match_set_diff,
    case_insensitive_partial_match_set_intersect,
    case_insensitive_set_diff,
    case_insensitive_set_intersect,
    get_packages,
    parse_licenses_list,
)
from tests import UNICODE_APPENDIX, CommandLineTestCase, PatchDistributionsTestCase


class ShouldIncludeFilesTestCase(CommandLineTestCase):
    KEYS = ["with_license_file", "with_license_files", "with_notice_file", "with_notice_files", "with_other_files"]

    def test_none_requested(self) -> None:
        args = CustomNamespace(**{key: False for key in self.KEYS})
        self.assertFalse(_should_include_files(args))

    def test_one_requested(self) -> None:
        args = CustomNamespace()

        def set_keys(_enabled: str) -> None:
            for _key in self.KEYS:
                setattr(args, _key, _key == _enabled)

        for name in self.KEYS:
            with self.subTest(name=name):
                set_keys(name)
                self.assertTrue(_should_include_files(args))

    def test_multiple_requested(self) -> None:
        args = CustomNamespace(**{key: key.endswith("s") for key in self.KEYS})
        self.assertTrue(_should_include_files(args))


class GetPackagesTestCase(PatchDistributionsTestCase):
    def test_without_filter(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args([])
        packages = list(get_packages(args))
        self.assertIn(UNICODE_APPENDIX, packages[-1].name)

    def test_with_default_filter(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args(["--filter-strings"])
        packages = list(get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1].name)

    def test_with_default_filter_and_license_file(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args(["--filter-strings", "--with-license-file"])
        packages = list(get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1].name)

    def test_with_specified_filter(self) -> None:
        self._patch_distributions()
        args = self.parser.parse_args(["--filter-strings", "--filter-code-page=ascii"])
        packages = list(get_packages(args))
        self.assertNotIn(UNICODE_APPENDIX, packages[-1].summary)


class ParseLicensesListTestCase(TestCase):
    def test_parse_licenses_list(self) -> None:
        licenses_str = " MIT License;;  MIT    ;  Apache-2.0;;;    "

        licenses = parse_licenses_list(licenses_str)

        self.assertListEqual(["MIT License", "MIT", "Apache-2.0"], licenses)


class CaseInsensitivePartialMatchSetDiffTestCase(TestCase):
    def test_case_insensitive_partial_match_set_diff(self) -> None:
        set_a = {"MIT License"}
        set_b = {"Mit", "BSD License"}
        set_c = {"mit license"}
        a_diff_b = case_insensitive_partial_match_set_diff(set_a, set_b)
        a_diff_c = case_insensitive_partial_match_set_diff(set_a, set_c)
        b_diff_c = case_insensitive_partial_match_set_diff(set_b, set_c)
        a_diff_empty = case_insensitive_partial_match_set_diff(set_a, set())

        self.assertSetEqual(set(), a_diff_b)
        self.assertSetEqual(set(), a_diff_c)
        self.assertIn("BSD License", b_diff_c)
        self.assertIn("MIT License", a_diff_empty)

    def test_no_overlap(self) -> None:
        """
        When no overlap, the result should be the same as set_a.
        """
        set_a = {"Python", "Java", "C++"}
        set_b = {"Ruby", "JavaScript"}
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual(set_a, result)

    def test_full_overlap(self) -> None:
        """
        When all items overlap, the result should be an empty set.
        """
        set_a = {"Hello", "World"}
        set_b = {"hello", "world"}
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual(set(), result)

    def test_partial_overlap(self) -> None:
        """
        Only 'Python' should remain as it has no overlap with set_b.
        """
        set_a = {"HelloWorld", "Python", "JavaScript"}
        set_b = {"hello", "script"}
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual({"Python"}, result)

    def test_case_insensitive(self) -> None:
        """
        The function should handle case-insensitive matches correctly.
        """
        set_a = {"HELLO", "world"}
        set_b = {"hello"}
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual({"world"}, result)

    def test_empty_sets(self) -> None:
        """
        When both sets are empty, the result should also be empty.
        """
        set_a: set[str] = set()
        set_b: set[str] = set()
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual(set(), result)

    def test_set_b_is_empty(self) -> None:
        """
        If set_b is empty, result should be the same as set_a.
        """
        set_a = {"Python", "Java"}
        set_b: set[str] = set()
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual(set_a, result)

    def test_set_a_is_empty(self) -> None:
        """
        If set_a is empty, result should be empty regardless of set_b.
        """
        set_a: set[str] = set()
        set_b = {"Ruby"}
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual(set(), result)

    def test_set_a_is_not_empty(self) -> None:
        """
        If set_b contains two similar substrings, there should be no double deletion.
        """
        set_a = {"Python 3.11", "Python 3.12", "Javascript"}
        set_b = {"Python", "Python 3"}
        result = case_insensitive_partial_match_set_diff(set_a, set_b)
        self.assertSetEqual({"Javascript"}, result)


class CaseInsensitiveSetDiffTestCase(TestCase):
    def test_case_insensitive_set_diff(self) -> None:
        set_a = {"MIT License"}
        set_b = {"Mit License", "BSD License"}
        set_c = {"mit license"}
        a_diff_b = case_insensitive_set_diff(set_a, set_b)
        a_diff_c = case_insensitive_set_diff(set_a, set_c)
        b_diff_c = case_insensitive_set_diff(set_b, set_c)
        a_diff_empty = case_insensitive_set_diff(set_a, set())

        self.assertSetEqual(set(), a_diff_b)
        self.assertSetEqual(set(), a_diff_c)
        self.assertIn("BSD License", b_diff_c)
        self.assertIn("MIT License", a_diff_empty)


class CaseInsensitiveSetIntersectTestCase(TestCase):
    def test_case_insensitive_set_intersect(self) -> None:
        set_a = {"Revised BSD"}
        set_b = {"Apache License", "revised BSD"}
        set_c = {"revised bsd"}
        a_intersect_b = case_insensitive_set_intersect(set_a, set_b)
        a_intersect_c = case_insensitive_set_intersect(set_a, set_c)
        b_intersect_c = case_insensitive_set_intersect(set_b, set_c)
        a_intersect_empty = case_insensitive_set_intersect(set_a, set())

        self.assertSetEqual(set_a, a_intersect_b)
        self.assertSetEqual(set_a, a_intersect_c)
        self.assertSetEqual({"revised BSD"}, b_intersect_c)
        self.assertSetEqual(set(), a_intersect_empty)


class CaseInsensitivePartialMatchSetIntersectTestCase(TestCase):
    def test_case_insensitive_partial_match_set_intersect(self) -> None:
        set_a = {"Revised BSD"}
        set_b = {"Apache License", "revised BSD"}
        set_c = {"bsd"}
        a_intersect_b = case_insensitive_partial_match_set_intersect(set_a, set_b)
        a_intersect_c = case_insensitive_partial_match_set_intersect(set_a, set_c)
        b_intersect_c = case_insensitive_partial_match_set_intersect(set_b, set_c)
        a_intersect_empty = case_insensitive_partial_match_set_intersect(set_a, set())

        self.assertSetEqual(set_a, a_intersect_b)
        self.assertSetEqual(set_a, a_intersect_c)
        self.assertSetEqual({"revised BSD"}, b_intersect_c)
        self.assertSetEqual(set(), a_intersect_empty)
