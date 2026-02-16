# Usage

## Command-Line Options

### Common options

#### Option: python

By default, this tools finds the packages from the environment pip-licenses-cli is launched from, by searching in current python's `sys.path` folders.
In case you want to search for packages in another environment (e.g., if you want to run pip-licenses-cli from its own isolated environment), you can
specify a path to a python executable. The packages will be searched for in the given python's `sys.path`, free of pip-licenses dependencies.

```bash
(venv) $ pip-licenses --with-system | grep pip
 pip                           22.3.1       MIT License
 pip-licenses-cli              4.1.0        MIT License
 pip-licenses-lib              0.5.0        MIT License
```

```bash
(venv) $ pip-licenses --python=</path/to/other/env>/bin/python --with-system | grep pip
 pip                       23.0.1       MIT License 
```

#### Option: from

By default, this tool finds the license from [Trove Classifiers](https://pypi.org/classifiers/) or package Metadata. Some Python packages declare their license only in
Trove Classifiers.

(See also): [Set license to MIT in setup.py by alisianoi ・ Pull Request #1058 ・ pypa/setuptools](https://github.com/pypa/setuptools/pull/1058), [PEP 314\#License](https://www.python.org/dev/peps/pep-0314/#license)

For example, even if you check with the `pip show` command, the license is displayed as `UNKNOWN`.

```bash
(venv) $ pip show setuptools
Name: setuptools
Version: 38.5.0
Summary: Easily download, build, install, upgrade, and uninstall Python packages
Home-page: https://github.com/pypa/setuptools
Author: Python Packaging Authority
Author-email: distutils-sig@python.org
License: UNKNOWN
```

The mixed mode (`--from=mixed`) of this tool works well and looks for licenses.

```bash
(venv) $ pip-licenses --from=mixed --with-system | grep setuptools
 setuptools    38.5.0   MIT License
```

In mixed mode, it first tries to look for licenses in the Trove Classifiers. When not found in the Trove Classifiers, the license declared in Metadata
is displayed.

If you want to look only in metadata, use `--from=meta`. If you want to look only in Trove Classifiers, use `--from=classifier`.

To list license information from both metadata and classifier, use `--from=all`.

**Note:** If neither can find license information, please check with the `with-authors` and `with-urls` options and contact the software author.

* The `m` keyword is prepared as alias of `meta`.
* The `c` keyword is prepared as alias of `classifier`.
* The `mix` keyword is prepared as alias of `mixed`.
    * Default behavior in this tool

#### Option: order

By default, it is ordered by package name.

If you give arguments to the `--order` option, you can output in another sort order.

```bash
(venv) $ pip-licenses --order=license
```

#### Option: format

By default, it is output to the `plain` format.

##### Markdown

When executed with the `--format=markdown` option, you can output list in Markdown format. The `m` `md` keyword is prepared as alias of `markdown`.

```bash
(venv) $ pip-licenses --format=markdown
| Name   | Version | License |
|--------|---------|---------|
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |
```

When inserted in a Markdown document, it is rendered as follows:

| Name   | Version | License |
|--------|---------|---------|
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |

##### reST

When executed with the `--format=rst` option, you can output list in "[Grid tables](http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#grid-tables)" of reStructuredText format. The `r` `rest` keyword is
prepared as alias of `rst`.

```bash
(venv) $ pip-licenses --format=rst
+--------+---------+---------+
| Name   | Version | License |
+--------+---------+---------+
| Django | 2.0.2   | BSD     |
+--------+---------+---------+
| pytz   | 2017.3  | MIT     |
+--------+---------+---------+
```

##### Confluence

When executed with the `--format=confluence` option, you can output list in [Confluence (or JIRA) Wiki markup](https://confluence.atlassian.com/doc/confluence-wiki-markup-251003035.html#ConfluenceWikiMarkup-Tables) format. The `c` keyword is
prepared as alias of `confluence`.

```bash
(venv) $ pip-licenses --format=confluence
| Name   | Version | License |
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |
```

##### HTML

When executed with the `--format=html` option, you can output list in HTML table format. The `h` keyword is prepared as alias of `html`.

```bash
(venv) $ pip-licenses --format=html
<table>
    <tr>
        <th>Name</th>
        <th>Version</th>
        <th>License</th>
    </tr>
    <tr>
        <td>Django</td>
        <td>2.0.2</td>
        <td>BSD</td>
    </tr>
    <tr>
        <td>pytz</td>
        <td>2017.3</td>
        <td>MIT</td>
    </tr>
</table>
```

##### JSON

When executed with the `--format=json` option, you can output list in JSON format easily allowing post-processing. The `j` keyword is prepared
as alias of `json`.

```json
[
  {
    "Author": "Django Software Foundation",
    "License": "BSD",
    "Name": "Django",
    "URL": "https://www.djangoproject.com/",
    "Version": "2.0.2"
  },
  {
    "Author": "Stuart Bishop",
    "License": "MIT",
    "Name": "pytz",
    "URL": "http://pythonhosted.org/pytz",
    "Version": "2017.3"
  }
]
```

##### JSON LicenseFinder

When executed with the `--format=json-license-finder` option, you can output list in JSON format that is identical to [LicenseFinder](https://github.com/pivotal/LicenseFinder).
The `jlf` keyword is prepared as alias of `jlf`.
This makes pip-licenses-cli a drop-in replacement for LicenseFinder.

```json
[
  {
    "licenses": ["BSD"],
    "name": "Django",
    "version": "2.0.2"
  },
  {
    "licenses": ["MIT"],
    "name": "pytz",
    "version": "2017.3"
  }
]

```

##### CSV

When executed with the `--format=csv` option, you can output list in quoted CSV format. Useful when you want to copy/paste the output to an Excel sheet.

```bash
(venv) $ pip-licenses --format=csv
"Name","Version","License"
"Django","2.0.2","BSD"
"pytz","2017.3","MIT"
```

##### Plain Vertical

When executed with the `--format=plain-vertical` option, you can output a simple plain vertical output that is similar to Angular CLI's
[--extractLicenses flag](https://angular.io/cli/build#options). This format minimizes rightward drift.

```bash
(venv) $ pip-licenses --format=plain-vertical --with-license-file --no-license-path
pytest
5.3.4
MIT license
The MIT License (MIT)

Copyright (c) 2004-2020 Holger Krekel and others

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### Option: summary

When executed with the `--summary` option, you can output a summary of each license.

```bash
(venv) $ pip-licenses --summary --from=classifier --with-system
 Count  License
 2      BSD License
 4      MIT License
```

**Note:** When using this option, only `--order=count` or `--order=license` has an effect for the `--order` option. And using `--with-authors`
and `--with-urls` will be ignored.

#### Option: output\-file

When executed with the `--output-file` option, write the result to the path specified by the argument.

```
(venv) $ pip-licenses --format=rst --output-file=/tmp/output.rst
created path: /tmp/output.rst
```

#### Option: ignore-packages

When executed with the `--ignore-packages` option, ignore the package specified by argument from list output.

```bash
(venv) $ pip-licenses --ignore-packages django
 Name  Version  License
 pytz  2017.3   MIT
```

Spaces can separate package names of arguments.

```bash
(venv) $ pip-licenses --with-system --ignore-packages django pip pip-licenses-cli pip-licenses-lib
 Name        Version  License
 prettytable 3.5.0    BSD License
 pytz        2017.3   MIT
 setuptools  38.5.0   UNKNOWN
 wcwidth     0.2.5    MIT License
```

Packages can also be specified with a version, only ignoring that specific version.

```bash
(venv) $ pip-licenses --with-system --ignore-packages django pytz:2017.3
 Name        Version  License
 prettytable 3.5.0    BSD License
 setuptools  38.5.0   UNKNOWN
 wcwidth     0.2.5    MIT License
```

#### Option: packages

When executed with the `packages` option, look at the package specified by argument from list output.

```bash
(venv) $ pip-licenses --packages django
 Name   Version  License
 Django 2.0.2    BSD
```

Spaces can separate package names of arguments.

```bash
(venv) $ pip-licenses --with-system --packages prettytable pytz
 Name        Version  License
 prettytable 3.5.0    BSD License
 pytz        2017.3   MIT
```

### Format options

#### Option: with-system

By default, system packages such as `pip` and `setuptools` are ignored.

And `pip-licenses-cli`, `pip-licenses-lib` and the implicit dependency `prettytable` and `wcwidth` will also be ignored.

If you want to output all including system package, use the `--with-system` option.

```bash
(venv) $ pip-licenses --with-system
 Name              Version  License
 Django            2.0.2    BSD
 pip               9.0.1    MIT
 pip-licenses-cli  1.0.0    MIT License
 pip-licenses-lib  0.5.0    MIT License
 prettytable       3.5.0    BSD License
 pytz              2017.3   MIT
 setuptools        38.5.0   UNKNOWN
 wcwidth           0.2.5    MIT License
```

#### Option: with-authors

When executed with the `--with-authors` option, output with author of the package.

```bash
(venv) $ pip-licenses --with-authors
 Name    Version  License  Author
 Django  2.0.2    BSD      Django Software Foundation
 pytz    2017.3   MIT      Stuart Bishop
```

#### Option: with-maintainers

When executed with the `--with-maintainers` option, output with maintainer of the package.

**Note:** This option is available for users who want information about the maintainer as well as the author. See [#144](https://github.com/raimon49/pip-licenses/issues/144)

#### Option: with-urls

For packages without Metadata, the license is output as `UNKNOWN`. To get more package information, use the `--with-urls` option.

```bash
(venv) $ pip-licenses --with-urls
 Name    Version  License  URL
 Django  2.0.2    BSD      https://www.djangoproject.com/
 pytz    2017.3   MIT      http://pythonhosted.org/pytz
```

#### Option: with-description

When executed with the `--with-description` option, output with short description of the package.

```bash
(venv) $ pip-licenses --with-description
 Name    Version  License  Description
 Django  2.0.2    BSD      A high-level Python Web framework that encourages rapid development and clean, pragmatic design.
 pytz    2017.3   MIT      World timezone definitions, modern and historical
```

#### Option: no-version

When executed with the `--no-version` option, output without the version number.

```bash
(venv) $ pip-licenses --no-version
 Name    License
 Django  BSD
 pytz    MIT
```

#### Option: with-license-file

When executed with the `--with-license-file` option, output the location of the package's license file on disk and the full contents of that file.
Due to the length of these fields, this option is best paired with `--format=json`.

If you also want to output the file `NOTICE` distributed under Apache License etc., specify the `--with-notice-file` option as well.

To emit all files in JSON and *plain-vertical* mode (instead of just the first one), use the following parameters:

  * `--with-license-files` emits all license files.
  * `--with-notice-files` emits all notice files.
  * `--with-other-files` emits all other licensing-related files not captured by the aforementioned groups, for example AUTHORS files.
  * `--with-sbom-files` emits all SBOM files (PEP 770).

**Note:** If you want to keep the corresponding file paths secret, specify `--no-license-path` option as well.

#### Option: filter\-strings

Some package data contains Unicode characters which might cause problems for certain output formats (in particular ReST tables). If this filter
is enabled, all characters that cannot be encoded with a given code page (see `--filter-code-page`) will be removed from any input strings (e.g.,
package name, description).

#### Option: filter\-code\-page

If the input strings are filtered (see `--filter-strings`), you can specify the applied code page (default `latin-1`). A list of all available
code pages can be found [codecs module document](https://docs.python.org/3/library/codecs.html#standard-encodings).


### Verify options

#### Option: fail\-on

Fail (exit with code 1) on the first occurrence of the licenses from the semicolon-separated list. The license name
matching is case-insensitive.

If `--from=all`, the option will apply to the metadata license field.

```bash
(venv) $ pip-licenses --fail-on="MIT License;BSD License"
```
**Note:** Packages with multiple licenses will fail if at least one license is included in the fail-on list. For example:
```
# keyring library has 2 licenses
$ pip-licenses --package keyring
 Name     Version  License
 keyring  23.0.1   MIT License; Python Software Foundation License

# If just "Python Software Foundation License" is specified, it will fail.
$ pip-licenses --package keyring --fail-on="Python Software Foundation License;"
$ echo $?
1

# Matching is case-insensitive. Following check will fail:
$ pip-licenses --fail-on="mit license"
```

#### Option: allow\-only

Fail (exit with code 1) if none of the package licenses are in the semicolon-separated list. The license name
matching is case-insensitive.

If `--from=all`, the option will apply to the metadata license field.

```bash
(venv) $ pip-licenses --allow-only="MIT License;BSD License"
```
**Note:** Packages with multiple licenses will only be allowed if at least one license is included in the allow-only list. For example:
```
# keyring library has 2 licenses
$ pip-licenses --package keyring
 Name     Version  License
 keyring  23.0.1   MIT License; Python Software Foundation License

# One or both licenses must be specified (order and case does not matter). Following checks will pass:
$ pip-licenses --package keyring --allow-only="MIT License"
$ pip-licenses --package keyring --allow-only="mit License"
$ pip-licenses --package keyring --allow-only="BSD License;MIT License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License;MIT License"

# If none of the license in the allow list match, the check will fail.
$ pip-licenses --package keyring  --allow-only="BSD License"
$ echo $?
1
```

#### Option: partial\-match

If set, enables partial (substring) matching for `--fail-on` or `--allow-only`. Default is unset (False).

Usage:

```bash
(venv) $ pip-licenses --partial-match --allow-only="MIT License;BSD License"
(venv) $ pip-licenses --partial-match --fail-on="MIT License;BSD License"

```

**Note:** Semantics are the same as with `--fail-on` or `--allow-only`. This only enables substring matching.
```
# keyring library has 2 licenses
$ pip-licenses --package keyring
 Name     Version  License
 keyring  23.0.1   MIT License; Python Software Foundation License

# One or both licenses must be specified (order and case does not matter). Following checks will pass:
$ pip-licenses --package keyring --allow-only="MIT License"
$ pip-licenses --package keyring --allow-only="mit License"
$ pip-licenses --package keyring --allow-only="BSD License;MIT License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License;MIT License"

# These won't pass, as they're not a full match against one of the licenses
$ pip-licenses --package keyring --allow-only="MIT"
$ echo $?
1
$ pip-licenses --package keyring --allow-only="mit"
$ echo $?
1

# with --partial-match, they pass
$ pip-licenses --package keyring --partial-match --allow-only="MIT"
$ echo $?
0
$ pip-licenses --package keyring --partial-match --allow-only="mit"
$ echo $?
0
```

#### Option: collect\-all\-failures

If set, collects all license failures and reports them after processing all packages.
Defaults to throwing an error after first failure.

### pyproject.toml support

All command-line options for `pip-licenses` can be configured using the `pyproject.toml` file under the `[tool.pip-licenses]` section. 
The `pyproject.toml` file is searched in the directory where the `pip-licenses` script is executed.
Command-line options specified during execution will override the corresponding options in `pyproject.toml`.

Example `pyproject.toml` configuration:

```toml
[tool.pip-licences]
from = "classifier"
ignore-packages = [
  "scipy"
]
fail-on = "MIT;"
```

If you run `pip-licenses` without any command-line options, all options will be taken from the `pyproject.toml` file. 
For instance, if you run `pip-licenses --from=mixed`, the `from` option will be overridden to `mixed`, while all other options will be sourced from
`pyproject.toml`.

### More Information

Other, please make sure to execute the `--help` option.

## Dockerfile

You can check the package license used by your app in the isolated Docker environment.

```bash
# Clone this repository to local
$ git clone https://github.com/stefan6419846/pip-licenses-cli.git
$ cd pip-licenses

# Create your app's requirements.txt file
# Other ways, pip freeze > docker/requirements.txt
$ echo "Flask" > docker/requirements.txt

# Build docker image
$ docker build . -t myapp-licenses

# Check the package license in container
$ docker run --rm myapp-licenses
 Name          Version  License
 Click         7.0      BSD License
 Flask         1.0.2    BSD License
 Jinja2        2.10     BSD License
 MarkupSafe    1.1.1    BSD License
 Werkzeug      0.15.2   BSD License
 itsdangerous  1.1.0    BSD License

# Check with options
$ docker run --rm myapp-licenses --summary
 Count  License
 4      BSD
 2      BSD-3-Clause

# When you need help
$ docker run --rm myapp-licenses --help
```

**Note:** This Docker image cannot check package licenses with C and C ++ Extensions. It only works with pure Python package dependencies.

If you want to resolve build environment issues, try using not slim image and more.

```diff
diff --git a/Dockerfile b/Dockerfile
index bfc4edc..175e968 100644
--- a/Dockerfile
+++ b/Dockerfile
@@ -1,4 +1,4 @@
-FROM python:3.11-slim-bullseye
+FROM python:3.11-bullseye
```
