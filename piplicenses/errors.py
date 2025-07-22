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


# Triggers F401 -- Unused -- kept for historical note
# see https://docs.python.org/3/library/warnings.html#module-warnings
# seealso https://docs.python.org/3/library/exceptions.html#UserWarning
# import warnings

# some code does not use *args, **keywords so they use lazy partial to load pre-calls
# see https://docs.python.org/3/library/functools.html#functools.partial
from functools import partial

from .cli import CustomNamespace
from .cli import FormatArg
from .constants import (
    AMBER,
    BOLD,
    RESET,
    PIP_LICENSE_CLI_WARN_MSG_NO_JSON_FILE,
    PIP_LICENSE_CLI_WARN_MSG_W_SUM_AND_ORDER,
)


def output_colored(code: str, text: str, is_bold: bool = False) -> str:
    """
    Create function to output with color sequence
    """
    if is_bold:
        code = f"{BOLD}{code}"

    return f"\033[{code}m{text}{RESET}"


class PipLicensesWarning(UserWarning):
    """
    Base class for warnings emitted by the pip-licenses-cli package.
    """


def create_warn_string(args: CustomNamespace) -> str:
    warn_messages: list = []
    _warn_out = partial(output_colored, code=AMBER)

    if args.with_license_file and not args.format_ == FormatArg.JSON:
        message = _warn_out(text=PIP_LICENSE_CLI_WARN_MSG_NO_JSON_FILE)
        warn_messages.append(message)

    if args.summary and (args.with_authors or args.with_urls):
        message = _warn_out(text=PIP_LICENSE_CLI_WARN_MSG_W_SUM_AND_ORDER)
        warn_messages.append(message)

    return "\n".join(warn_messages)
