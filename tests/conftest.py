import sys
from pathlib import Path

import pytest

# Let tests import the project files
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session", autouse=True)
def docker_running():
    import docker
    try:
        docker.from_env().ping()
    except Exception:
        pytest.exit(
            "Docker is not running. Open Docker Desktop, wait for 'Engine running', then try again.",
            returncode=1,
        )
