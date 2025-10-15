# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2018 raimon
# SPDX-FileCopyrightText: Copyright (c) 2025 stefan6419846

from __future__ import annotations

import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from functools import cached_property
from importlib.metadata import Distribution
from io import StringIO
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Optional, Type
from unittest import TestCase

import piplicenses_lib

from piplicenses.cli import create_parser

if TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from importlib.metadata._meta import PackageMetadata
    else:
        from email.message import Message as PackageMetadata


TESTS_PATH = Path(__file__).resolve().parent
FIXTURES_PATH = TESTS_PATH / "fixtures"

# Read from external file considering a terminal that cannot handle "emoji"
UNICODE_APPENDIX = FIXTURES_PATH.joinpath("unicode_characters.txt").read_text(encoding="utf-8").replace("\n", "")

importlib_metadata_distributions_orig = piplicenses_lib.importlib_metadata.distributions


def importlib_metadata_distributions_mocked(*args: Any, **kwargs: Any) -> list[Distribution]:
    class DistributionMocker(Distribution):
        def __init__(self, orig_dist: Distribution) -> None:
            self.__dist = orig_dist

        @property
        def metadata(self) -> PackageMetadata:
            return EmailMessageMocker(self.__dist.metadata)

        def locate_file(self, path: str | os.PathLike[str]):
            return self.__dist.locate_file(path)

        def read_text(self, filename) -> str | None:
            return self.__dist.read_text(filename)

    class EmailMessageMocker(Message):
        def __init__(self, orig_msg: PackageMetadata) -> None:
            super().__init__()
            self.__msg = orig_msg

        def __getattr__(self, attr: str) -> Any:
            return getattr(self.__msg, attr)

        def __getitem__(self, key: str) -> Any:
            if key.lower() == "name":
                return self.__msg["name"] + " " + UNICODE_APPENDIX
            return self.__msg[key]

    packages = list(importlib_metadata_distributions_orig(*args, **kwargs))
    packages[-1] = DistributionMocker(packages[-1])  # type: ignore[abstract]
    return packages


class CaptureOutput:
    def __init__(self) -> None:
        self._stdout_buffer: StringIO = StringIO()
        self._stderr_buffer: StringIO = StringIO()

    def __enter__(self) -> "CaptureOutput":
        self._stdout_redirect = redirect_stdout(self._stdout_buffer)
        self._stderr_redirect = redirect_stderr(self._stderr_buffer)
        self._stdout_redirect.__enter__()
        self._stderr_redirect.__enter__()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> None:
        self._stderr_redirect.__exit__(exception_type, exception_value, exception_traceback)
        self._stdout_redirect.__exit__(exception_type, exception_value, exception_traceback)

    @cached_property
    def stdout(self) -> str:
        return self._stdout_buffer.getvalue()

    @cached_property
    def stderr(self) -> str:
        return self._stderr_buffer.getvalue()


class CommandLineTestCase(TestCase):
    parser = create_parser()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.parser = create_parser()


class PatchDistributionsTestCase(CommandLineTestCase):
    def _patch_distributions(self) -> None:
        def cleanup():
            piplicenses_lib.importlib_metadata.distributions = importlib_metadata_distributions_orig

        self.addCleanup(cleanup)
        piplicenses_lib.importlib_metadata.distributions = importlib_metadata_distributions_mocked
