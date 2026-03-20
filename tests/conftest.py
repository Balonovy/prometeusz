import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
os.environ.setdefault('MOCK_LLM', 'true')
os.environ.setdefault('SQLITE_PATH', 'data/test_prometeusz.db')

import pytest

from interfaces.api.dependencies import get_app_container


@pytest.fixture(autouse=True)
def reset_container_cache():
    get_app_container.cache_clear()
    yield
    get_app_container.cache_clear()
