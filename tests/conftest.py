import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "seed"))

from generator import generate  # noqa: E402


@pytest.fixture(scope="session")
def dataset():
    return generate()
