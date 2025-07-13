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


def case_insensitive_set_intersect(set_a, set_b) -> set:
    """Same as set.intersection() but case-insensitive"""
    common_items = set()
    set_b_lower = {item.lower() for item in set_b}
    for elem in set_a:
        if elem.lower() in set_b_lower:
            common_items.add(elem)
    return common_items


def case_insensitive_partial_match_set_intersect(set_a, set_b) -> set:
    common_items = set()
    for item_a in set_a:
        for item_b in set_b:
            if item_b.lower() in item_a.lower():
                common_items.add(item_a)
    return common_items


def case_insensitive_partial_match_set_diff(set_a, set_b) -> set:
    uncommon_items = set_a.copy()
    for item_a in set_a:
        for item_b in set_b:
            if item_b.lower() in item_a.lower():
                uncommon_items.discard(item_a)
    return uncommon_items


def case_insensitive_set_diff(set_a, set_b) -> set:
    uncommon_items = set()
    set_b_lower = {item.lower() for item in set_b}
    for elem in set_a:
        if not elem.lower() in set_b_lower:
            uncommon_items.add(elem)
    return uncommon_items
