"""
Statehouse client implementation

This module provides a clean Python API that hides all gRPC/protobuf details.
"""

from typing import Any, Dict, Iterator, Optional

import grpc
from google.protobuf.struct_pb2 import Struct

# Import generated stubs
from ._generated.statehouse.v1 import statehouse_pb2, statehouse_pb2_grpc
from .exceptions import ConnectionError as StatehouseConnectionError
from .exceptions import StatehouseError, TransactionError
from .types import Operation, ReplayEvent, StateResult


class Transaction:
    """
    A transaction context for staging writes and deletes.

    Usage:
        tx = client.begin_transaction()
        tx.write(agent_id="agent-1", key="memory", value={"fact": "..."})
        tx.commit()
    """

    def __init__(self, client: "Statehouse", txn_id: str, namespace: str = "default"):
        self._client = client
        self._txn_id = txn_id
        self._namespace = namespace
        self._committed = False
        self._aborted = False

    def write(self, agent_id: str, key: str, value: Dict[str, Any]) -> None:
        """
        Stage a write operation.

        Args:
            agent_id: Agent identifier
            key: State key
            value: JSON-compatible value (dict)
        """
        if self._committed or self._aborted:
            raise TransactionError("Transaction already finalized")

        self._client._write(self._txn_id, self._namespace, agent_id, key, value)

    def delete(self, agent_id: str, key: str) -> None:
        """
        Stage a delete operation.

        Args:
            agent_id: Agent identifier
            key: State key
        """
        if self._committed or self._aborted:
            raise TransactionError("Transaction already finalized")

        self._client._delete(self._txn_id, self._namespace, agent_id, key)

    def commit(self) -> int:
        """
        Commit the transaction atomically.

        Returns:
            commit_ts: Commit timestamp
        """
        if self._committed:
            raise TransactionError("Transaction already committed")
        if self._aborted:
            raise TransactionError("Transaction already aborted")

        commit_ts = self._client._commit(self._txn_id)
        self._committed = True
        return commit_ts

    def abort(self) -> None:
        """Abort the transaction, discarding all staged operations."""
        if self._committed:
            raise TransactionError("Cannot abort: transaction already committed")
        if self._aborted:
            return  # Idempotent

        self._client._abort(self._txn_id)
        self._aborted = True

    def __enter__(self) -> "Transaction":
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-commit on success, auto-abort on exception."""
        if exc_type is None and not self._committed and not self._aborted:
            self.commit()
        elif not self._committed and not self._aborted:
            self.abort()


class Statehouse:
    """
    Statehouse client.

    This is the main entry point for interacting with the Statehouse daemon.
    All gRPC/protobuf details are hidden from the user.

    Example:
        client = Statehouse(url="localhost:50051")

        # Write
        with client.begin_transaction() as tx:
            tx.write(agent_id="agent-1", key="memory", value={"fact": "..."})

        # Read
        state = client.get_state(agent_id="agent-1", key="memory")
        print(state.value)
    """

    def __init__(self, url: str = "localhost:50051", namespace: str = "default"):
        """
        Initialize Statehouse client.

        Args:
            url: Daemon address (host:port)
            namespace: Default namespace (default: "default")
        """
        self._url = url
        self._namespace = namespace
        self._channel = None
        self._stub = None
        self._connect()

    def _connect(self) -> None:
        """Establish gRPC connection."""
        try:
            self._channel = grpc.insecure_channel(self._url)
            self._stub = statehouse_pb2_grpc.StatehouseServiceStub(self._channel)
        except Exception as e:
            raise StatehouseConnectionError(f"Failed to connect to {self._url}: {e}")

    def health(self) -> str:
        """
        Check daemon health.

        Returns:
            Health status string
        """
        try:
            request = statehouse_pb2.HealthRequest()
            response = self._stub.Health(request)
            return response.status
        except grpc.RpcError as e:
            raise StatehouseConnectionError(f"Health check failed: {e}")

    def version(self) -> tuple[str, str]:
        """
        Get daemon version.

        Returns:
            (version, git_sha) tuple
        """
        try:
            request = statehouse_pb2.VersionRequest()
            response = self._stub.Version(request)
            return response.version, response.git_sha
        except grpc.RpcError as e:
            raise StatehouseError(f"Version check failed: {e}")

    def begin_transaction(self, timeout_ms: Optional[int] = None, namespace: Optional[str] = None) -> Transaction:
        """
        Begin a new transaction.

        Args:
            timeout_ms: Transaction timeout in milliseconds (default: 30000)
            namespace: Namespace (default: instance default)

        Returns:
            Transaction object
        """
        try:
            request = statehouse_pb2.BeginTransactionRequest(timeout_ms=timeout_ms)
            response = self._stub.BeginTransaction(request)
            txn_id = response.txn_id
            return Transaction(self, txn_id, namespace or self._namespace)
        except grpc.RpcError as e:
            raise TransactionError(f"Failed to begin transaction: {e}")

    def _write(self, txn_id: str, namespace: str, agent_id: str, key: str, value: Dict[str, Any]) -> None:
        """Internal: stage write operation."""
        try:
            struct_value = _dict_to_struct(value)
            request = statehouse_pb2.WriteRequest(
                txn_id=txn_id,
                namespace=namespace,
                agent_id=agent_id,
                key=key,
                value=struct_value,
            )
            self._stub.Write(request)
        except grpc.RpcError as e:
            raise TransactionError(f"Write failed: {e}")

    def _delete(self, txn_id: str, namespace: str, agent_id: str, key: str) -> None:
        """Internal: stage delete operation."""
        try:
            request = statehouse_pb2.DeleteRequest(
                txn_id=txn_id,
                namespace=namespace,
                agent_id=agent_id,
                key=key,
            )
            self._stub.Delete(request)
        except grpc.RpcError as e:
            raise TransactionError(f"Delete failed: {e}")

    def _commit(self, txn_id: str) -> int:
        """Internal: commit transaction."""
        try:
            request = statehouse_pb2.CommitRequest(txn_id=txn_id)
            response = self._stub.Commit(request)
            return response.commit_ts
        except grpc.RpcError as e:
            raise TransactionError(f"Commit failed: {e}")

    def _abort(self, txn_id: str) -> None:
        """Internal: abort transaction."""
        try:
            request = statehouse_pb2.AbortRequest(txn_id=txn_id)
            self._stub.Abort(request)
        except grpc.RpcError as e:
            raise TransactionError(f"Abort failed: {e}")

    def get_state(self, agent_id: str, key: str, namespace: Optional[str] = None) -> StateResult:
        """
        Read latest state for a key.

        Args:
            agent_id: Agent identifier
            key: State key
            namespace: Namespace (default: instance default)

        Returns:
            StateResult with value, version, commit_ts, exists
        """
        try:
            request = statehouse_pb2.GetStateRequest(
                namespace=namespace or self._namespace,
                agent_id=agent_id,
                key=key,
            )
            response = self._stub.GetState(request)
            value = _struct_to_dict(response.value) if response.HasField("value") else None
            return StateResult(
                value=value,
                version=response.version,
                commit_ts=response.commit_ts,
                exists=response.exists,
            )
        except grpc.RpcError as e:
            raise StatehouseError(f"GetState failed: {e}")

    def get_state_at_version(
        self, agent_id: str, key: str, version: int, namespace: Optional[str] = None
    ) -> StateResult:
        """
        Read state at a specific version.

        Args:
            agent_id: Agent identifier
            key: State key
            version: Version number
            namespace: Namespace (default: instance default)

        Returns:
            StateResult
        """
        try:
            request = statehouse_pb2.GetStateAtVersionRequest(
                namespace=namespace or self._namespace,
                agent_id=agent_id,
                key=key,
                version=version,
            )
            response = self._stub.GetStateAtVersion(request)
            value = _struct_to_dict(response.value) if response.HasField("value") else None
            return StateResult(
                value=value,
                version=response.version,
                commit_ts=response.commit_ts,
                exists=response.exists,
            )
        except grpc.RpcError as e:
            raise StatehouseError(f"GetStateAtVersion failed: {e}")

    def list_keys(self, agent_id: str, namespace: Optional[str] = None) -> list[str]:
        """
        List all keys for an agent.

        Args:
            agent_id: Agent identifier
            namespace: Namespace (default: instance default)

        Returns:
            List of keys
        """
        try:
            request = statehouse_pb2.ListKeysRequest(
                namespace=namespace or self._namespace,
                agent_id=agent_id,
            )
            response = self._stub.ListKeys(request)
            return list(response.keys)
        except grpc.RpcError as e:
            raise StatehouseError(f"ListKeys failed: {e}")

    def scan_prefix(self, agent_id: str, prefix: str, namespace: Optional[str] = None) -> list[StateResult]:
        """
        Scan keys with a prefix.

        Args:
            agent_id: Agent identifier
            prefix: Key prefix
            namespace: Namespace (default: instance default)

        Returns:
            List of StateResult objects
        """
        try:
            request = statehouse_pb2.ScanPrefixRequest(
                namespace=namespace or self._namespace,
                agent_id=agent_id,
                prefix=prefix,
            )
            response = self._stub.ScanPrefix(request)
            results = []
            for entry in response.entries:
                value = _struct_to_dict(entry.value)
                results.append(
                    StateResult(
                        value=value,
                        version=entry.version,
                        commit_ts=entry.commit_ts,
                        exists=True,
                    )
                )
            return results
        except grpc.RpcError as e:
            raise StatehouseError(f"ScanPrefix failed: {e}")

    def replay(
        self,
        agent_id: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> Iterator[ReplayEvent]:
        """
        Replay events for an agent.

        Args:
            agent_id: Agent identifier
            start_ts: Start timestamp (optional)
            end_ts: End timestamp (optional)
            namespace: Namespace (default: instance default)

        Yields:
            ReplayEvent objects
        """
        try:
            request = statehouse_pb2.ReplayRequest(
                namespace=namespace or self._namespace,
                agent_id=agent_id,
                start_ts=start_ts,
                end_ts=end_ts,
            )
            for event in self._stub.Replay(request):
                operations = []
                for op in event.operations:
                    value = _struct_to_dict(op.value) if op.HasField("value") else None
                    operations.append(
                        Operation(
                            key=op.key,
                            value=value,
                            version=op.version,
                        )
                    )
                yield ReplayEvent(
                    txn_id=event.txn_id,
                    commit_ts=event.commit_ts,
                    operations=operations,
                    namespace=namespace or self._namespace,
                    agent_id=agent_id,
                )
        except grpc.RpcError as e:
            raise StatehouseError(f"Replay failed: {e}")

    def replay_events(
        self,
        agent_id: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> Iterator[ReplayEvent]:
        """
        Replay events for an agent (alias for replay()).

        This method is identical to replay() but provided for clarity
        when using alongside replay_pretty().

        Args:
            agent_id: Agent identifier
            start_ts: Start timestamp (optional)
            end_ts: End timestamp (optional)
            namespace: Namespace (default: instance default)

        Yields:
            ReplayEvent objects
        """
        return self.replay(agent_id, start_ts, end_ts, namespace)

    def replay_pretty(
        self,
        agent_id: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        namespace: Optional[str] = None,
        verbose: bool = False,
    ) -> Iterator[str]:
        """
        Replay events with pretty formatting (human-readable).

        This is the recommended way to display replay output to users.
        Each event's operations are formatted as single-line strings.

        Args:
            agent_id: Agent identifier
            start_ts: Start timestamp (optional)
            end_ts: End timestamp (optional)
            namespace: Namespace (default: instance default)
            verbose: If True, include full details (txn_id, event_id, payload)

        Yields:
            Formatted event strings (one per operation)
        """
        from .formatting import format_event_pretty, format_event_verbose

        for event in self.replay(agent_id, start_ts, end_ts, namespace):
            for i, op in enumerate(event.operations):
                if verbose:
                    # Verbose format with full details
                    line = format_event_verbose(
                        timestamp=event.commit_ts,
                        agent_id=agent_id,
                        operation="write" if op.value is not None else "delete",
                        key=op.key,
                        version=op.version,
                        txn_id=event.txn_id,
                        event_id=i,  # Operation index within transaction
                        value=op.value,
                        namespace=namespace or self._namespace,
                    )
                else:
                    # Standard pretty format
                    line = format_event_pretty(
                        timestamp=event.commit_ts,
                        agent_id=agent_id,
                        operation="write" if op.value is not None else "delete",
                        key=op.key,
                        version=op.version,
                        value=op.value,
                        namespace=namespace or self._namespace,
                    )
                yield line

    def close(self) -> None:
        """Close the connection."""
        if self._channel:
            self._channel.close()

    def __enter__(self) -> "Statehouse":
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-close connection."""
        self.close()


# Helper functions for protobuf Struct <-> dict conversion


def _dict_to_struct(d: Dict[str, Any]) -> Struct:
    """Convert dict to protobuf Struct."""
    struct = Struct()
    struct.update(d)
    return struct


def _struct_to_dict(struct: Struct) -> Dict[str, Any]:
    """Convert protobuf Struct to dict."""
    return dict(struct)
