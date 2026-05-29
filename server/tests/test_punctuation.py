"""Tests for punctuation restoration utility."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.punctuation import restore_punctuation, _PUNCT
from src.engines.base import WordTimestamp


def test_punct_set_excludes_space():
    assert " " not in _PUNCT


def test_restore_punctuation_basic():
    words = [
        WordTimestamp("你好", 0.0, 0.5),
        WordTimestamp("世界", 0.6, 1.0),
    ]
    full_text = "你好，世界！"

    result = restore_punctuation(words, full_text)
    assert "你好，" in result[0].text or result[0].text.endswith("，")
    assert "世界！" in result[1].text or result[1].text.endswith("！")


def test_restore_punctuation_empty_words():
    assert restore_punctuation([], "hello world") == []


def test_restore_punctuation_empty_text():
    words = [WordTimestamp("hello", 0.0, 0.5)]
    assert restore_punctuation(words, "") == [WordTimestamp("hello", 0.0, 0.5)]


def test_restore_punctuation_no_punctuation():
    words = [WordTimestamp("hello", 0.0, 0.5), WordTimestamp("world", 0.6, 1.0)]
    full_text = "helloworld"

    result = restore_punctuation(words, full_text)
    assert len(result) == 2
    assert result[0].text == "hello"
    assert result[1].text == "world"


def test_restore_punctuation_english():
    words = [
        WordTimestamp("Hello", 0.0, 0.5),
        WordTimestamp("world", 0.6, 1.0),
    ]
    full_text = "Hello, world!"

    result = restore_punctuation(words, full_text)
    assert len(result) == 2
