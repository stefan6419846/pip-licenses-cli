# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

from __future__ import annotations

import sys
from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from piplicenses_lib import get_packages as _get_packages
from piplicenses_lib import normalize_package_name

from piplicenses.constants import SYSTEM_PACKAGES
from piplicenses.spdx import _parse_spdx

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterator

    from piplicenses_lib import PackageInfo

    from piplicenses.cli import CustomNamespace


def parse_licenses_list(licenses_str: str | None) -> list[str]:
    if licenses_str is None:
        return []

    licenses = licenses_str.split(";")

    # Strip items
    licenses = list(map(str.strip, licenses))

    # Remove empty string items
    licenses = list(filter(None, licenses))

    return licenses


def get_packages(
    args: CustomNamespace,
) -> Iterator[PackageInfo]:
    ignore_pkgs_as_normalize = [normalize_package_name(pkg) for pkg in args.ignore_packages]
    pkgs_as_normalize = [normalize_package_name(pkg) for pkg in args.packages]

    fail_on_licenses = set(parse_licenses_list(args.fail_on))
    allow_only_licenses = set(parse_licenses_list(args.allow_only))

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


def case_insensitive_set_intersect(set_a, set_b):
    """Same as set.intersection() but case-insensitive"""
    common_items = set()
    set_b_lower = {item.lower() for item in set_b}
    for elem in set_a:
        if elem.lower() in set_b_lower:
            common_items.add(elem)
    return common_items


def case_insensitive_partial_match_set_intersect(set_a, set_b):
    common_items = set()
    for item_a in set_a:
        for item_b in set_b:
            if item_b.lower() in item_a.lower():
                common_items.add(item_a)
    return common_items


def case_insensitive_partial_match_set_diff(set_a, set_b):
    uncommon_items = set_a.copy()
    for item_a in set_a:
        for item_b in set_b:
            if item_b.lower() in item_a.lower():
                uncommon_items.discard(item_a)
    return uncommon_items


def case_insensitive_set_diff(set_a, set_b):
    """Same as set.difference() but case-insensitive"""
    uncommon_items = set()
    set_b_lower = {item.lower() for item in set_b}
    for elem in set_a:
        if elem.lower() not in set_b_lower:
            uncommon_items.add(elem)
    return uncommon_items
