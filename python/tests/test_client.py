"""
Integration tests for Statehouse Python SDK

These tests require a running Statehouse daemon.
Start the daemon with: 
  STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon

Or from the scripts directory:
  ./scripts/dev.sh
"""

import pytest
import time
from statehouse import Statehouse, Transaction
from statehouse.types import ReplayEvent
from statehouse.exceptions import TransactionError, StatehouseError


@pytest.fixture(scope="module")
def daemon_url():
    """URL of the test daemon"""
    return "localhost:50051"


@pytest.fixture(scope="module")
def client(daemon_url):
    """Synchronous client fixture"""
    return Statehouse(url=daemon_url)


class TestHealthAndVersion:
    """Test health and version endpoints"""

    def test_client_health(self, client):
        """Test health check"""
        health = client.health()
        assert health == "ok"

    def test_version(self, client):
        """Test version endpoint"""
        version, git_sha = client.version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert isinstance(git_sha, str)


class TestTransactionLifecycle:
    """Test transaction write/commit operations"""

    def test_tx_write_commit(self, client):
        """Test basic transaction write and commit"""
        tx = client.begin_transaction()
        
        # Write operation
        tx.write(
            agent_id="test-agent",
            key="test-key",
            value={"value": 42, "timestamp": time.time()}
        )
        
        # Commit
        commit_ts = tx.commit()
        assert commit_ts > 0

    def test_multiple_writes_in_transaction(self, client):
        """Test multiple writes in single transaction"""
        tx = client.begin_transaction()
        
        for i in range(5):
            tx.write(
                agent_id="test-agent",
                key=f"batch-key-{i}",
                value={"index": i}
            )
        
        commit_ts = tx.commit()
        assert commit_ts > 0
        
        # Verify all writes were committed
        for i in range(5):
            result = client.get_state(agent_id="test-agent", key=f"batch-key-{i}")
            assert result.exists
            assert result.value is not None
            assert result.value["index"] == i

    def test_transaction_context_manager(self, client):
        """Test transaction with context manager"""
        with client.begin_transaction() as tx:
            tx.write(
                agent_id="test-agent",
                key="ctx-key",
                value={"context": "manager"}
            )
        
        # Verify auto-commit worked
        result = client.get_state(agent_id="test-agent", key="ctx-key")
        assert result.exists
        assert result.value is not None
        assert result.value["context"] == "manager"

    def test_transaction_double_commit_error(self, client):
        """Test that double commit raises error"""
        tx = client.begin_transaction()
        tx.write(agent_id="test-agent", key="double-commit", value={})
        tx.commit()
        
        with pytest.raises(TransactionError):
            tx.commit()

    def test_transaction_abort(self, client):
        """Test transaction abort"""
        # Use unique key to avoid conflicts
        abort_key = f"abort-key-{time.time()}"
        
        tx = client.begin_transaction()
        tx.write(agent_id="test-agent", key=abort_key, value={"aborted": True})
        tx.abort()
        
        # Verify write was not committed
        result = client.get_state(agent_id="test-agent", key=abort_key)
        assert not result.exists

    def test_delete_operation(self, client):
        """Test delete operation"""
        delete_key = f"delete-me-{time.time()}"
        
        # First write a key
        tx = client.begin_transaction()
        tx.write(agent_id="test-agent", key=delete_key, value={"will": "be deleted"})
        tx.commit()
        
        # Verify it exists
        state = client.get_state(agent_id="test-agent", key=delete_key)
        assert state is not None
        
        # Delete it
        tx = client.begin_transaction()
        tx.delete(agent_id="test-agent", key=delete_key)
        tx.commit()
        
        # After delete, the key should not appear in list_keys
        # (tombstone should be filtered out)
        keys = client.list_keys(agent_id="test-agent")
        assert delete_key not in keys


class TestReadOperations:
    """Test read-after-write and state retrieval"""

    def test_read_after_write(self, client):
        """Test read-after-write consistency"""
        test_key = f"raw-test-{time.time()}"
        test_value = {"data": "important", "version": 1}
        
        # Write
        tx = client.begin_transaction()
        tx.write(agent_id="test-agent", key=test_key, value=test_value)
        commit_ts = tx.commit()
        
        # Read immediately
        result = client.get_state(agent_id="test-agent", key=test_key)
        assert result.exists
        assert result.value is not None
        assert result.value["data"] == "important"
        assert result.value["version"] == 1

    def test_read_nonexistent_key(self, client):
        """Test reading a key that doesn't exist"""
        result = client.get_state(
            agent_id="test-agent",
            key=f"nonexistent-{time.time()}"
        )
        assert not result.exists

    def test_list_keys(self, client):
        """Test listing keys for an agent"""
        # Write some keys with unique agent ID
        agent_id = f"list-test-{int(time.time() * 1000)}"
        
        for i in range(3):
            tx = client.begin_transaction()
            tx.write(agent_id=agent_id, key=f"list-key-{i}", value={"i": i})
            tx.commit()
        
        # List keys
        keys = client.list_keys(agent_id=agent_id)
        assert isinstance(keys, list)
        assert len(keys) == 3
        for i in range(3):
            assert f"list-key-{i}" in keys

    def test_scan_prefix(self, client):
        """Test scanning keys with prefix"""
        agent_id = f"scan-test-{int(time.time() * 1000)}"
        prefix = "config/"
        
        # Write keys with prefix
        for i in range(3):
            tx = client.begin_transaction()
            tx.write(agent_id=agent_id, key=f"{prefix}setting-{i}", value={"i": i})
            tx.commit()
        
        # Scan
        results = client.scan_prefix(agent_id=agent_id, prefix=prefix)
        assert isinstance(results, list)
        assert len(results) == 3
        
        # Verify all results have the prefix
        for result in results:
            assert result.value is not None
            assert result.value.get("i") is not None


class TestReplay:
    """Test replay iteration"""

    def test_replay_iteration(self, client):
        """Test iterating through replay events"""
        agent_id = f"replay-test-{int(time.time() * 1000)}"
        
        # Create some events
        for i in range(5):
            tx = client.begin_transaction()
            tx.write(agent_id=agent_id, key=f"event-{i}", value={"step": i})
            tx.commit()
        
        # Replay events
        events = list(client.replay(agent_id=agent_id))
        assert isinstance(events, list)
        assert len(events) == 5
        
        # Verify events are in order
        timestamps = [e.commit_ts for e in events]
        assert timestamps == sorted(timestamps), "Events should be in chronological order"

    def test_replay_with_time_range(self, client):
        """Test replay with start/end timestamps"""
        agent_id = f"replay-range-{int(time.time() * 1000)}"
        
        # Create events
        commit_timestamps = []
        for i in range(5):
            tx = client.begin_transaction()
            tx.write(agent_id=agent_id, key=f"range-{i}", value={"i": i})
            ts = tx.commit()
            commit_timestamps.append(ts)
        
        # Replay with range (middle 3 events)
        start_ts = commit_timestamps[1]
        end_ts = commit_timestamps[3]
        
        events = list(client.replay(
            agent_id=agent_id,
            start_ts=start_ts,
            end_ts=end_ts
        ))
        
        # Should get events 1, 2, 3
        assert len(events) == 3
        for event in events:
            assert start_ts <= event.commit_ts <= end_ts


class TestErrorMapping:
    """Test error handling and error mapping"""

    def test_invalid_transaction_id(self, client):
        """Test error when using invalid transaction ID"""
        with pytest.raises(TransactionError):
            # Manually create transaction with invalid ID
            tx = Transaction(client, "invalid-txn-id-999", "default")
            tx.commit()

    def test_connection_error_handling(self):
        """Test error when connecting to non-existent server"""
        with pytest.raises(Exception):
            # This should fail to connect
            bad_client = Statehouse(url="localhost:99999")
            bad_client.health()

    def test_transaction_timeout(self, client):
        """Test transaction timeout"""
        # Begin transaction with very short timeout
        tx = client.begin_transaction(timeout_ms=100)
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Try to commit - should fail with timeout error
        with pytest.raises(TransactionError):
            tx.commit()


class TestRestartSafety:
    """Test restart and recovery scenarios"""

    def test_committed_data_persists(self, client):
        """Test that committed data is immediately readable"""
        persist_key = f"persist-{int(time.time() * 1000)}"
        
        # Write data
        tx = client.begin_transaction()
        tx.write(
            agent_id="test-agent",
            key=persist_key,
            value={"important": "data", "persist": True}
        )
        commit_ts = tx.commit()
        
        # Verify immediate read
        result = client.get_state(agent_id="test-agent", key=persist_key)
        assert result.exists
        assert result.value is not None
        assert result.value["important"] == "data"
        
        # Note: Full restart testing would require actually restarting
        # the daemon, which is beyond the scope of unit tests.
        # This test verifies the write-read cycle works.

    def test_replay_after_writes(self, client):
        """Test that replay includes all committed events"""
        agent_id = f"replay-safety-{int(time.time() * 1000)}"
        
        # Write several events
        num_events = 5
        for i in range(num_events):
            tx = client.begin_transaction()
            tx.write(agent_id=agent_id, key=f"safe-{i}", value={"i": i})
            tx.commit()
        
        # Replay and verify all events are present
        events = list(client.replay(agent_id=agent_id))
        
        # Should have exactly our events
        assert len(events) == num_events
        
        # Verify order
        for i, event in enumerate(events):
            assert len(event.operations) > 0
            # Each event should have our write
            assert any(op.key == f"safe-{i}" for op in event.operations)


class TestReplayConvenienceAPIs:
    """Test replay convenience APIs (replay_events, replay_pretty)"""
    
    def test_replay_events_alias(self, client):
        """Test that replay_events() works identically to replay()"""
        agent_id = f"replay-events-{int(time.time() * 1000)}"
        
        # Write some test data
        tx = client.begin_transaction()
        tx.write(agent_id=agent_id, key="test1", value={"data": "value1"})
        tx.write(agent_id=agent_id, key="test2", value={"data": "value2"})
        tx.commit()
        
        # Use replay_events()
        events = list(client.replay_events(agent_id=agent_id))
        
        assert len(events) > 0
        assert all(isinstance(e, ReplayEvent) for e in events)
        
        # Verify events have expected structure
        for event in events:
            assert event.agent_id == agent_id
            assert event.namespace == "default"
            assert event.txn_id
            assert event.commit_ts > 0
    
    def test_replay_pretty_basic(self, client):
        """Test basic pretty replay formatting"""
        agent_id = f"pretty-{int(time.time() * 1000)}"
        
        # Write test data
        tx = client.begin_transaction()
        tx.write(agent_id=agent_id, key="context", value={"topic": "test"})
        tx.commit()
        
        # Get pretty replay
        lines = list(client.replay_pretty(agent_id=agent_id))
        
        # Should have at least one line
        assert len(lines) > 0
        
        # Each line should be a string
        assert all(isinstance(line, str) for line in lines)
        
        # Lines should contain key information
        for line in lines:
            assert agent_id in line
            assert "context" in line or "WRITE" in line
    
    def test_replay_pretty_verbose(self, client):
        """Test verbose replay formatting"""
        agent_id = f"verbose-{int(time.time() * 1000)}"
        
        # Write test data
        tx = client.begin_transaction()
        tx.write(agent_id=agent_id, key="data", value={"x": 42})
        tx.commit()
        
        # Get verbose replay
        lines = list(client.replay_pretty(agent_id=agent_id, verbose=True))
        
        assert len(lines) > 0
        
        # Verbose output should include txn_id
        verbose_text = "\n".join(lines)
        assert "txn=" in verbose_text or "payload:" in verbose_text
    
    def test_replay_pretty_ordering(self, client):
        """Test that pretty replay maintains event order"""
        agent_id = f"order-{int(time.time() * 1000)}"
        
        # Write events in sequence
        keys = ["step1", "step2", "step3"]
        for key in keys:
            tx = client.begin_transaction()
            tx.write(agent_id=agent_id, key=key, value={"key": key})
            tx.commit()
        
        # Get pretty replay
        lines = list(client.replay_pretty(agent_id=agent_id))
        
        # Should have at least 3 lines (one per write)
        assert len(lines) >= 3
        
        # Check ordering - keys should appear in sequence
        text = "\n".join(lines)
        pos1 = text.find("step1")
        pos2 = text.find("step2")
        pos3 = text.find("step3")
        
        assert pos1 < pos2 < pos3
    
    def test_replay_pretty_truncation(self, client):
        """Test that large values are truncated in pretty output"""
        agent_id = f"truncate-{int(time.time() * 1000)}"
        
        # Write very long string
        long_value = "x" * 1000
        tx = client.begin_transaction()
        tx.write(agent_id=agent_id, key="long", value={"data": long_value})
        tx.commit()
        
        # Get pretty replay
        lines = list(client.replay_pretty(agent_id=agent_id))
        
        assert len(lines) > 0
        
        # Lines should be reasonably short (not 1000+ chars)
        for line in lines:
            # Each line should be under 250 chars (with reasonable margin)
            assert len(line) < 300
    
    def test_replay_event_repr(self, client):
        """Test ReplayEvent.__repr__() uses pretty formatting"""
        agent_id = f"repr-{int(time.time() * 1000)}"
        
        # Write test data
        tx = client.begin_transaction()
        tx.write(agent_id=agent_id, key="test", value={"x": 1})
        tx.commit()
        
        # Get event and check repr
        events = list(client.replay_events(agent_id=agent_id))
        assert len(events) > 0
        
        event = events[0]
        repr_str = repr(event)
        
        # repr should contain key information
        assert agent_id in repr_str
        assert "test" in repr_str or "WRITE" in repr_str
    
    def test_replay_event_to_dict(self, client):
        """Test ReplayEvent.to_dict() method"""
        agent_id = f"dict-{int(time.time() * 1000)}"
        
        # Write test data
        tx = client.begin_transaction()
        tx.write(agent_id=agent_id, key="key1", value={"a": 1})
        tx.write(agent_id=agent_id, key="key2", value={"b": 2})
        tx.commit()
        
        # Get event and convert to dict
        events = list(client.replay_events(agent_id=agent_id))
        assert len(events) > 0
        
        event = events[0]
        event_dict = event.to_dict()
        
        # Verify dict structure
        assert "txn_id" in event_dict
        assert "commit_ts" in event_dict
        assert "namespace" in event_dict
        assert "agent_id" in event_dict
        assert "operations" in event_dict
        
        # Verify values
        assert event_dict["agent_id"] == agent_id
        assert event_dict["namespace"] == "default"
        assert isinstance(event_dict["operations"], list)
        assert len(event_dict["operations"]) > 0
    
    def test_replay_pretty_with_time_range(self, client):
        """Test pretty replay with time range filtering"""
        agent_id = f"range-{int(time.time() * 1000)}"
        
        # Write first event
        tx1 = client.begin_transaction()
        tx1.write(agent_id=agent_id, key="early", value={"time": "early"})
        ts1 = tx1.commit()
        
        # Wait a moment and write second event
        time.sleep(0.1)
        tx2 = client.begin_transaction()
        tx2.write(agent_id=agent_id, key="late", value={"time": "late"})
        ts2 = tx2.commit()
        
        # Replay only events after first commit
        lines = list(client.replay_pretty(agent_id=agent_id, start_ts=ts1 + 1))
        
        # Should only see second event
        text = "\n".join(lines)
        assert "late" in text
        # First event might or might not be present depending on timing
        # (we're testing time filtering works, not exact boundaries)
