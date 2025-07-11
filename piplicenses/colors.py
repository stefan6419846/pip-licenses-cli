# pip-licenses-cli
#
# MIT License
#
# Copyright (c) 2018 raimon
# Copyright (c) 2025 stefan6419846
# Copyright (c) 2025 reactive-firewall
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


"""
ANSI Color Codes Module

This module defines constants for ANSI color codes used for formatting
text output in terminal applications. It includes foreground and
background color codes, as well as a reset code and a bold code.
"""

# ANSI Color Codes
RESET: str = "\033[0m"  # Reset all attributes to default
BOLD: str = "1;"  # Bold text attribute

# Foreground Colors
BLACK: str = "30"  # Black foreground color
RED: str = "31"  # Red foreground color
GREEN: str = "32"  # Green foreground color
AMBER: str = "33"  # Yellow/Amber foreground color
BLUE: str = "34"  # Blue foreground color
MAGENTA: str = "35"  # Magenta/Pink foreground color
CYAN: str = "36"  # Cyan/Teal foreground color
WHITE: str = "37"  # White foreground color

# Background Colors
BG_BLACK: str = "40"  # Black background color
BG_RED: str = "41"  # Red background color
BG_GREEN: str = "42"  # Green background color
BG_AMBER: str = "43"  # Yellow/Amber background color
BG_BLUE: str = "44"  # Blue background color
BG_MAGENTA: str = "45"  # Magenta/Pink background color
BG_CYAN: str = "46"  # Cyan/Teal background color
BG_WHITE: str = "47"  # White background color


def output_colored(code: str, text: str, is_bold: bool = False) -> str:
    """
    Format text with ANSI color codes for terminal output.

    This function applies a specified color code to the given text,
    optionally making the text bold. The formatted text can be used
    for colored output in terminal applications.

    Args:
        code (str): The ANSI color code to apply to the text.
        text (str): The text to be formatted with the color code.
        is_bold (bool, optional): If True, the text will be bold.
            Defaults to False.

    Returns:
        str: The formatted text with ANSI color codes.
    """
    if is_bold:
        code = f"{BOLD}{code}"

    return f"\033[{code}m{text}{RESET}"
