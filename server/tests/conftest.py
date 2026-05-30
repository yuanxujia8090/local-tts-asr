"""Pytest configuration — add src to Python path and cleanup test artifacts."""

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def _cleanup_custom_voices():
    """Remove all test artifacts from custom_voices directory after tests."""
    voices_dir = Path(__file__).parent.parent / "custom_voices"
    if not voices_dir.exists():
        return

    index_path = voices_dir / "voices.json"
    # Reset index to empty list
    if index_path.exists():
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump([], f)

    # Remove all audio files (anything that's not voices.json)
    for entry in os.listdir(voices_dir):
        if entry != "voices.json":
            filepath = voices_dir / entry
            try:
                if filepath.is_file():
                    filepath.unlink()
                elif filepath.is_dir():
                    shutil.rmtree(filepath)
            except OSError:
                pass


def pytest_sessionfinish(session, exitstatus):
    """Cleanup custom_voices after all tests finish."""
    _cleanup_custom_voices()
