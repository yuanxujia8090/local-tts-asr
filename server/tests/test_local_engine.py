"""Tests for _language_to_code in local_engine."""

from src.engines.local_engine import _language_to_code


def test_language_to_code_chinese():
    assert _language_to_code("Chinese") == "Chinese"
    assert _language_to_code("chinese") == "Chinese"
    assert _language_to_code("CHINESE") == "Chinese"


def test_language_to_code_english():
    assert _language_to_code("English") == "English"
    assert _language_to_code("english") == "English"


def test_language_to_code_japanese():
    assert _language_to_code("Japanese") == "Japanese"
    assert _language_to_code("japanese") == "Japanese"


def test_language_to_code_korean():
    assert _language_to_code("Korean") == "Korean"


def test_language_to_code_german():
    assert _language_to_code("German") == "German"


def test_language_to_code_french():
    assert _language_to_code("French") == "French"


def test_language_to_code_russian():
    assert _language_to_code("Russian") == "Russian"


def test_language_to_code_none():
    assert _language_to_code(None) is None
    assert _language_to_code("") is None


def test_language_to_code_unknown():
    # Unknown language should be capitalized first letter
    assert _language_to_code("spanish") == "Spanish"
    assert _language_to_code("German") == "German"


def test_language_to_code_auto():
    # "Auto" is not in the mapping — should be capitalized as-is
    result = _language_to_code("Auto")
    assert result == "Auto"
