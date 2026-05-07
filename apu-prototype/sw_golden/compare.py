from __future__ import annotations

from typing import Iterable, Sequence


def compare_sequences(actual: Sequence[int], expected: Sequence[int]) -> None:
    if list(actual) != list(expected):
        raise AssertionError(f'mismatch: actual={list(actual)} expected={list(expected)}')
