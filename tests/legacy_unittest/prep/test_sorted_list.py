# -*- coding: utf-8 -*-
# Copyright 2019 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import copy

import pytest

from iconservice.prep.data.sorted_list import SortedList, Sortable


class SortedItem(Sortable):
    def __init__(self, value: int):
        self.value = value

    def order(self):
        return self.value


def check_sorted_list(items: 'SortedList'):
    prev_item = None

    for item in items:
        assert isinstance(item, Sortable)
        if prev_item:
            assert prev_item.order() <= item.order()

        prev_item = item

@pytest.fixture
def create_sorted_list():
    def _create_sorted_list(size: int):
        items = SortedList()

        for i in range(size):
            item = SortedItem(random.randint(-10000, 10000))
            items.add(item)

        assert len(items) == size
        return items

    return _create_sorted_list


def test_add(create_sorted_list):
    size = 100
    items = create_sorted_list(size)
    check_sorted_list(items)

    item = SortedItem(random.randint(-9999, 9999))
    items.add(item)
    assert len(items) == size + 1
    check_sorted_list(items)


def test_remove(create_sorted_list):
    for size in (1, 99, 100):
        items = create_sorted_list(size)
        assert len(items) == size

        index: int = random.randint(0, size - 1)
        item = items[index]
        assert item is not None
        removed_item = items.remove(item)
        assert item == removed_item
        assert len(items) == size - 1
        check_sorted_list(items)

    item = SortedItem(0)
    items = SortedList()
    assert len(items) == 0

    with pytest.raises(ValueError):
        items.remove(item)


def test_remove_with_same_order_items(create_sorted_list):
    size = 100
    items = create_sorted_list(size)
    assert len(items) == size

    index: int = random.randint(0, size - 1)

    for _ in range(10):
        item = items[index]
        copied_item = copy.copy(item)
        items._items.insert(index, copied_item)

    check_sorted_list(items)

    for _ in range(10):
        size = len(items)

        item = items[index]
        assert item is not None

        removed_item = items.remove(item)
        assert item == removed_item
        assert len(items) == size - 1

        with pytest.raises(ValueError):
            items.remove(item)

        check_sorted_list(items)


def test_pop(create_sorted_list):
    for size in (1, 99, 100):
        items = create_sorted_list(size)

        index: int = random.randint(0, size - 1)
        item = items[index]

        popped_item = items.pop(index)
        assert item == popped_item
        assert len(items) == size - 1
        check_sorted_list(items)

    items = SortedList()
    assert len(items) == 0

    with pytest.raises(IndexError):
        items.pop(0)


def test_index(create_sorted_list):
    for size in (1, 2, 99, 100):
        items = create_sorted_list(size)

        indexes = set()
        indexes.add(0)
        indexes.add(max(0, size - 1))
        if size - 2 > 1:
            indexes.add(random.randint(1, size - 2))

        for index in indexes:
            i = items.index(items[index])
            assert i == index


def test_index_with_the_same_order_items(create_sorted_list):
    size = 100
    base_index = 30
    items = create_sorted_list(size)

    for _ in range(10):
        item = items[base_index]
        copied_item = copy.copy(item)
        items._items.insert(base_index, copied_item)

    check_sorted_list(items)

    for i in range(10):
        item = items[base_index + i]
        index: int = items.index(item)
        assert index == base_index + i
        assert id(item) == id(items[index])


def test__setitem__(create_sorted_list):
    items = create_sorted_list(1)

    item0: 'SortedItem' = items[0]
    new_item = SortedItem(value=item0.value + 1)
    items[0] = new_item

    assert id(new_item) == id(items[0])
    assert item0.value + 1 == items[0].value

    # Case 1
    items = create_sorted_list(2)
    item0: 'SortedItem' = items[0]
    item1: 'SortedItem' = items[1]

    new_item0 = SortedItem(item1.value - 1)
    items[0] = new_item0
    assert item0 != items[0]
    assert new_item0 == items[0]

    new_item0 = SortedItem(items[1].value + 1)
    with pytest.raises(ValueError):
        items[0] = new_item0

    new_item1 = SortedItem(items[0].value - 1)
    with pytest.raises(ValueError):
        items[1] = new_item1

    new_item1 = SortedItem(items[0].value + 1)
    items[1] = new_item1
    assert new_item1 == items[1]

    # Case 2
    items = create_sorted_list(3)

    new_item1 = SortedItem(items[0].value - 1)
    with pytest.raises(ValueError):
        items[1] = new_item1

    new_item1 = SortedItem(items[2].value + 1)
    with pytest.raises(ValueError):
        items[1] = new_item1

    new_item1 = SortedItem(items[0].value)
    items[1] = new_item1
    assert items[1] == new_item1

    new_item1 = SortedItem(items[2].value)
    items[1] = new_item1
    assert items[1] == new_item1


def test_append(create_sorted_list):
    items = create_sorted_list(size=0)

    for i in range(100):
        item = SortedItem(value=i)
        items.append(item)

        assert item == items[len(items) - 1]

    with pytest.raises(ValueError):
        last_item: SortedItem = items[len(items) - 1]
        item = SortedItem(value=last_item.value - 1)
        items.append(item)