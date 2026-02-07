from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ErrorCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[ErrorCode]
    INVALID_REQUEST: _ClassVar[ErrorCode]
    TXN_NOT_FOUND: _ClassVar[ErrorCode]
    TXN_EXPIRED: _ClassVar[ErrorCode]
    TXN_ALREADY_COMMITTED: _ClassVar[ErrorCode]
    KEY_NOT_FOUND: _ClassVar[ErrorCode]
    VERSION_NOT_FOUND: _ClassVar[ErrorCode]
    STORAGE_ERROR: _ClassVar[ErrorCode]
    INTERNAL_ERROR: _ClassVar[ErrorCode]
UNKNOWN: ErrorCode
INVALID_REQUEST: ErrorCode
TXN_NOT_FOUND: ErrorCode
TXN_EXPIRED: ErrorCode
TXN_ALREADY_COMMITTED: ErrorCode
KEY_NOT_FOUND: ErrorCode
VERSION_NOT_FOUND: ErrorCode
STORAGE_ERROR: ErrorCode
INTERNAL_ERROR: ErrorCode

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class VersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class VersionResponse(_message.Message):
    __slots__ = ("version", "git_sha")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    GIT_SHA_FIELD_NUMBER: _ClassVar[int]
    version: str
    git_sha: str
    def __init__(self, version: _Optional[str] = ..., git_sha: _Optional[str] = ...) -> None: ...

class BeginTransactionRequest(_message.Message):
    __slots__ = ("timeout_ms",)
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    timeout_ms: int
    def __init__(self, timeout_ms: _Optional[int] = ...) -> None: ...

class BeginTransactionResponse(_message.Message):
    __slots__ = ("txn_id",)
    TXN_ID_FIELD_NUMBER: _ClassVar[int]
    txn_id: str
    def __init__(self, txn_id: _Optional[str] = ...) -> None: ...

class WriteRequest(_message.Message):
    __slots__ = ("txn_id", "namespace", "agent_id", "key", "value")
    TXN_ID_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    txn_id: str
    namespace: str
    agent_id: str
    key: str
    value: _struct_pb2.Struct
    def __init__(self, txn_id: _Optional[str] = ..., namespace: _Optional[str] = ..., agent_id: _Optional[str] = ..., key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class WriteResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteRequest(_message.Message):
    __slots__ = ("txn_id", "namespace", "agent_id", "key")
    TXN_ID_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    txn_id: str
    namespace: str
    agent_id: str
    key: str
    def __init__(self, txn_id: _Optional[str] = ..., namespace: _Optional[str] = ..., agent_id: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class DeleteResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CommitRequest(_message.Message):
    __slots__ = ("txn_id",)
    TXN_ID_FIELD_NUMBER: _ClassVar[int]
    txn_id: str
    def __init__(self, txn_id: _Optional[str] = ...) -> None: ...

class CommitResponse(_message.Message):
    __slots__ = ("commit_ts",)
    COMMIT_TS_FIELD_NUMBER: _ClassVar[int]
    commit_ts: int
    def __init__(self, commit_ts: _Optional[int] = ...) -> None: ...

class AbortRequest(_message.Message):
    __slots__ = ("txn_id",)
    TXN_ID_FIELD_NUMBER: _ClassVar[int]
    txn_id: str
    def __init__(self, txn_id: _Optional[str] = ...) -> None: ...

class AbortResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetStateRequest(_message.Message):
    __slots__ = ("namespace", "agent_id", "key")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    agent_id: str
    key: str
    def __init__(self, namespace: _Optional[str] = ..., agent_id: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class GetStateResponse(_message.Message):
    __slots__ = ("value", "version", "commit_ts", "exists")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TS_FIELD_NUMBER: _ClassVar[int]
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    value: _struct_pb2.Struct
    version: int
    commit_ts: int
    exists: bool
    def __init__(self, value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., version: _Optional[int] = ..., commit_ts: _Optional[int] = ..., exists: bool = ...) -> None: ...

class GetStateAtVersionRequest(_message.Message):
    __slots__ = ("namespace", "agent_id", "key", "version")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    agent_id: str
    key: str
    version: int
    def __init__(self, namespace: _Optional[str] = ..., agent_id: _Optional[str] = ..., key: _Optional[str] = ..., version: _Optional[int] = ...) -> None: ...

class GetStateAtVersionResponse(_message.Message):
    __slots__ = ("value", "version", "commit_ts", "exists")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TS_FIELD_NUMBER: _ClassVar[int]
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    value: _struct_pb2.Struct
    version: int
    commit_ts: int
    exists: bool
    def __init__(self, value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., version: _Optional[int] = ..., commit_ts: _Optional[int] = ..., exists: bool = ...) -> None: ...

class ListKeysRequest(_message.Message):
    __slots__ = ("namespace", "agent_id")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    agent_id: str
    def __init__(self, namespace: _Optional[str] = ..., agent_id: _Optional[str] = ...) -> None: ...

class ListKeysResponse(_message.Message):
    __slots__ = ("keys",)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, keys: _Optional[_Iterable[str]] = ...) -> None: ...

class ScanPrefixRequest(_message.Message):
    __slots__ = ("namespace", "agent_id", "prefix")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    agent_id: str
    prefix: str
    def __init__(self, namespace: _Optional[str] = ..., agent_id: _Optional[str] = ..., prefix: _Optional[str] = ...) -> None: ...

class ScanPrefixResponse(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[StateEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[StateEntry, _Mapping]]] = ...) -> None: ...

class StateEntry(_message.Message):
    __slots__ = ("key", "value", "version", "commit_ts")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TS_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: _struct_pb2.Struct
    version: int
    commit_ts: int
    def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., version: _Optional[int] = ..., commit_ts: _Optional[int] = ...) -> None: ...

class ReplayRequest(_message.Message):
    __slots__ = ("namespace", "agent_id", "start_ts", "end_ts")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    START_TS_FIELD_NUMBER: _ClassVar[int]
    END_TS_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    agent_id: str
    start_ts: int
    end_ts: int
    def __init__(self, namespace: _Optional[str] = ..., agent_id: _Optional[str] = ..., start_ts: _Optional[int] = ..., end_ts: _Optional[int] = ...) -> None: ...

class ReplayEvent(_message.Message):
    __slots__ = ("txn_id", "commit_ts", "operations")
    TXN_ID_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TS_FIELD_NUMBER: _ClassVar[int]
    OPERATIONS_FIELD_NUMBER: _ClassVar[int]
    txn_id: str
    commit_ts: int
    operations: _containers.RepeatedCompositeFieldContainer[Operation]
    def __init__(self, txn_id: _Optional[str] = ..., commit_ts: _Optional[int] = ..., operations: _Optional[_Iterable[_Union[Operation, _Mapping]]] = ...) -> None: ...

class Operation(_message.Message):
    __slots__ = ("key", "value", "version")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: _struct_pb2.Struct
    version: int
    def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., version: _Optional[int] = ...) -> None: ...

class StatehouseError(_message.Message):
    __slots__ = ("code", "message", "details")
    class DetailsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    code: ErrorCode
    message: str
    details: _containers.ScalarMap[str, str]
    def __init__(self, code: _Optional[_Union[ErrorCode, str]] = ..., message: _Optional[str] = ..., details: _Optional[_Mapping[str, str]] = ...) -> None: ...
