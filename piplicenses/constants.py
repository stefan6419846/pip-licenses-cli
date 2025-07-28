# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

import sys

from piplicenses import __pkgname__

FIELD_NAMES = (
    "Name",
    "Version",
    "License",
    "LicenseFile",
    "LicenseText",
    "NoticeFile",
    "NoticeText",
    "Author",
    "Maintainer",
    "Description",
    "URL",
)


SUMMARY_FIELD_NAMES = (
    "Count",
    "License",
)


DEFAULT_OUTPUT_FIELDS = (
    "Name",
    "Version",
)


SUMMARY_OUTPUT_FIELDS = (
    "Count",
    "License",
)

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


# Not using __pkgname__ because we want to be backwards compatible
TOML_SECTION_NAME = "pip-licenses"
