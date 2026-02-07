"""
pytest configuration for Statehouse tests
"""

import pytest
import grpc


def pytest_configure(config):
    """Check if daemon is running before running tests"""
    # We'll skip this check and let individual tests handle connection errors
    pass


@pytest.fixture(scope="session", autouse=True)
def check_daemon():
    """Check if the Statehouse daemon is accessible"""
    try:
        # Try to connect
        channel = grpc.insecure_channel("localhost:50051")
        grpc.channel_ready_future(channel).result(timeout=2)
        channel.close()
        print("\n✅ Statehouse daemon is running")
    except Exception as e:
        pytest.skip(
            f"Statehouse daemon not accessible at localhost:50051. "
            f"Start it with: STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon\n"
            f"Error: {e}"
        )
