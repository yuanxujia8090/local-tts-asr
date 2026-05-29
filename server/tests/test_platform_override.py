"""Tests for platform detection with ENGINE_MODE override."""

import os


def test_get_backend_with_engine_mode_local():
    """ENGINE_MODE=local should return 'local'."""
    with os.environ.pop('ENGINE_MODE', None) if 'ENGINE_MODE' in os.environ else type('', (), {'__enter__': lambda s: None, '__exit__': lambda s, *a: None})() as _:
        os.environ['ENGINE_MODE'] = 'local'
    try:
        from src.utils.platform import get_backend
        assert get_backend() == 'local'
    finally:
        os.environ.pop('ENGINE_MODE', None)


def test_get_backend_with_engine_mode_remote():
    """ENGINE_MODE=remote should return 'remote'."""
    os.environ['ENGINE_MODE'] = 'remote'
    try:
        from src.utils.platform import get_backend
        assert get_backend() == 'remote'
    finally:
        os.environ.pop('ENGINE_MODE', None)


def test_get_backend_label_for_remote():
    """get_backend_label should return 'remote' label."""
    os.environ['ENGINE_MODE'] = 'remote'
    try:
        from src.utils.platform import get_backend_label
        label = get_backend_label()
        assert 'remote' in label.lower()
    finally:
        os.environ.pop('ENGINE_MODE', None)
