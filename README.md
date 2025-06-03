# pip-licenses-cli

Dump the software license list of Python packages installed with *pip*.

## Description

`pip-licenses-cli` is a CLI tool for checking the software licenses of installed Python packages with pip.

Implemented with the idea inspired by `composer licenses` command in Composer (a.k.a PHP package management tool):
https://getcomposer.org/doc/03-cli.md#licenses

This is a fork of the original [pip-licenses](https://github.com/raimon49/pip-licenses) project. While `pip-licenses-cli` provides a CLI,
[pip-licenses-lib](https://github.com/stefan6419846/pip-licenses-lib) provides the library functionality. The CLI builds upon the library.

## Installation

You can install this package from PyPI:

```bash
python -m pip install pip-licenses-cli
```

If you want to additionally parse license declarations with [SPDX expressions](https://peps.python.org/pep-0639/#spdx-license-expression-syntax), then also install the `spdx` extra:

```bash
python -m pip install 'pip-licenses-cli[spdx]'
```

Alternatively, you can use the package from source directly after installing the required dependencies.

## Usage

Execute the command with your venv (or virtualenv) environment.

```bash
# Install packages in your venv environment
(venv) $ pip install Django pip-licenses-cli

# Check the licenses with your venv environment
(venv) $ pip-licenses
 Name    Version  License
 Django  2.0.2    BSD
 pytz    2017.3   MIT
```

For further details, see [the detailed docs](https://github.com/stefan6419846/pip-licenses-cli/blob/master/USAGE.md).

## About UnicodeEncodeError

If a `UnicodeEncodeError` occurs, check your environment variables `LANG` and `LC_TYPE`.
Additionally, you can set `PYTHONIOENCODING` to override the encoding used for `stdout`.

This mostly occurs in isolated environments such as Docker and tox.

See useful reports:

* [#35](https://github.com/raimon49/pip-licenses/issues/35)
* [#45](https://github.com/raimon49/pip-licenses/issues/45)

### Dependencies

`pip-licenses-cli` has been implemented in the policy to minimize the dependencies on external packages.

* [pip-licenses-cli](https://pypi.org/project/pip-licenses-cli/) by the same authors as the CLI (MIT License).
* [prettytable](https://pypi.org/project/prettytable/) by Luke Maurits, subject to the BSD-3-Clause License.
    * **Note:** This package implicitly requires [wcwidth](https://pypi.org/project/wcwidth/) by Jeff Quast (MIT License).
* For Python < 3.11: [tomli](https://pypi.org/project/tomli/) by Taneli Hukkinen under the MIT License.

If you are using SPDX support with the `spdx` extra, the following additional dependencies are required:

* [license-expression](https://pypi.org/project/license-expression/) by nexB Inc. under the Apache-2.0 License.
* [boolean.py](https://pypi.org/project/boolean.py/) by Sebastian Krämer under the BSD-2-Clause License.

## Contributing

See [contribution guidelines](https://github.com/stefan6419846/pip-licenses-cli/blob/master/CONTRIBUTING.md).


## License

This package is subject to the terms of the MIT license.

## Disclaimer

All results are generated automatically from the data supplied by the corresponding package maintainers and provided on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. No generated content should be considered or used as legal advice.
Consult an Attorney for any legal advice.
