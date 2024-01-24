"""pytest plugin configuration.

https://docs.pytest.org/en/latest/writing_plugins.html#conftest-py-plugins
"""
# Standard Python Libraries
import os
import time

# Third-Party Libraries
import docker
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import pytest

MONGO_INITDB_ROOT_USERNAME = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "mongoadmin")
MONGO_INITDB_ROOT_PASSWORD = os.environ.get("MONGO_INITDB_ROOT_PASSWORD", "secret")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "test")

docker_client = docker.from_env()


@pytest.fixture(autouse=True)
def group_github_log_lines(request):
    """Group log lines when running in GitHub actions."""
    # Group output from each test with workflow log groups
    # https://help.github.com/en/actions/reference/workflow-commands-for-github-actions#grouping-log-lines

    if os.environ.get("GITHUB_ACTIONS") != "true":
        # Not running in GitHub actions
        yield
        return
    # Group using the current test name
    print()
    print(f"::group::{request.node.name}")
    yield
    print()
    print("::endgroup::")


@pytest.fixture(scope="session")
def mongodb_container(mongo_image_tag):
    """Fixture for the MongoDB test container."""
    container = docker_client.containers.run(
        mongo_image_tag,
        detach=True,
        environment={
            "MONGO_INITDB_ROOT_USERNAME": MONGO_INITDB_ROOT_USERNAME,
            "MONGO_INITDB_ROOT_PASSWORD": MONGO_INITDB_ROOT_PASSWORD,
        },
        name="mongodb",
        ports={"27017/tcp": None},
        volumes={},
        healthcheck={
            "test": ["CMD", "mongosh", "--eval", "'db.runCommand(\"ping\").ok'"],
            "interval": 1000000000,  # ns -> 1 second
            "timeout": 1000000000,  # ns -> 1 second
            "retries": 5,
            "start_period": 3000000000,  # ns -> 3 seconds
        },
    )
    TIMEOUT = 180
    # Wait for container to be healthy
    for _ in range(TIMEOUT):
        # Verify the container is still running
        container.reload()
        assert container.status == "running", "The container unexpectedly exited."
        status = container.attrs["State"]["Health"]["Status"]
        if status == "healthy":
            break
        time.sleep(1)
    else:
        assert (
            False
        ), f"Container status did not transition to 'healthy' within {TIMEOUT} seconds."

    yield container
    container.stop()
    container.remove(force=True)


@pytest.fixture(scope="session")
def mongodb_engine(mongodb_container):
    """Fixture for the MongoDB engine."""
    mongo_port = mongodb_container.attrs["NetworkSettings"]["Ports"]["27017/tcp"][0][
        "HostPort"
    ]
    mongo_uri = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@localhost:{mongo_port}"

    client = AsyncIOMotorClient(mongo_uri)
    engine = AIOEngine(client=client, database=DATABASE_NAME)
    return engine


def pytest_addoption(parser):
    """Add new commandline options to pytest."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--mongo-image-tag",
        action="store",
        default="docker.io/mongo:latest",
        help="mongodb image tag to use for testing",
    )


@pytest.fixture(scope="session")
def mongo_image_tag(request):
    """Get the image tag to test."""
    return request.config.getoption("--mongo-image-tag")


def pytest_configure(config):
    """Register new markers."""
    config.addinivalue_line("markers", "slow: mark test as slow")


def pytest_collection_modifyitems(config, items):
    """Modify collected tests based on custom marks and commandline options."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
