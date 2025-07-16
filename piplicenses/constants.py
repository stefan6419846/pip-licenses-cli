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

from . import __pkgname__  # noqa: F401
from . import __version__  # noqa: F401

__summary__ = "Dump the software license list of Python packages installed with pip."

# ANSI Color Codes
RESET: str = "\033[0m"  # Reset all attributes to default
BOLD: str = "1;"  # Bold text attribute

# Foreground Colors
AMBER: str = "33"  # Yellow/Amber foreground color

# Warning string constants
PIP_LICENSE_CLI_WARN_MSG_SPDX_UNSUPPORTED_CLAUSE: str = "SPDX expressions with 'AND' or 'WITH' are currently not supported."
PIP_LICENSE_CLI_WARN_MSG_NO_JSON_FILE: str = "Due to the length of these fields, this option is best paired with --format=json."

PIP_LICENSE_CLI_WARN_MSG_W_SUM_AND_ORDER: str = str(
    "When using this option, only --order=count or --order=license has an effect for the --order "
    "option. And using --with-authors and --with-urls will be ignored."
)


# toml [tool.pip-licenses] section name
# Not using __pkgname__ because we want to be backwards compatible
TOML_SECTION_NAME: str = "pip-licenses"


# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS: dict = {
    "URL": "homepage",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "LicenseFile": "license_files",
    "LicenseText": "license_texts",
    "NoticeFile": "notice_files",
    "NoticeText": "notice_texts",
    "Description": "summary",
}

FIELD_NAMES: tuple = (
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


SUMMARY_FIELD_NAMES: tuple = (
    "Count",
    "License",
)


DEFAULT_OUTPUT_FIELDS: tuple = (
    "Name",
    "Version",
)


SUMMARY_OUTPUT_FIELDS: tuple = (
    "Count",
    "License",
)


SYSTEM_PACKAGES: list[str] = [
    __pkgname__,
    "pip",
    "pip-licenses-lib",
    "prettytable",
    "wcwidth",
    "setuptools",
    "wheel",
]
