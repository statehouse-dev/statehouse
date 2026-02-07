// gRPC service implementation

use anyhow::Result;
use std::sync::Arc;
use tonic::{Request, Response, Status};
use tokio_stream::wrappers::ReceiverStream;

use statehouse_proto::*;
use statehouse_core::state_machine::StateMachine;

pub struct StatehouseServiceImpl {
    state_machine: Arc<StateMachine>,
}

impl StatehouseServiceImpl {
    pub fn new(state_machine: Arc<StateMachine>) -> Self {
        Self { state_machine }
    }
}

#[tonic::async_trait]
impl statehouse_service_server::StatehouseService for StatehouseServiceImpl {
    async fn health(&self, _request: Request<HealthRequest>) -> Result<Response<HealthResponse>, Status> {
        Ok(Response::new(HealthResponse {
            status: "ok".to_string(),
        }))
    }

    async fn version(&self, _request: Request<VersionRequest>) -> Result<Response<VersionResponse>, Status> {
        Ok(Response::new(VersionResponse {
            version: env!("CARGO_PKG_VERSION").to_string(),
            git_sha: option_env!("GIT_SHA").unwrap_or("dev").to_string(),
        }))
    }

    async fn begin_transaction(&self, request: Request<BeginTransactionRequest>) -> Result<Response<BeginTransactionResponse>, Status> {
        let req = request.into_inner();
        let txn_id = self.state_machine.begin_transaction(req.timeout_ms)
            .map_err(|e| Status::internal(format!("Failed to begin transaction: {}", e)))?;

        Ok(Response::new(BeginTransactionResponse { txn_id }))
    }

    async fn write(&self, request: Request<WriteRequest>) -> Result<Response<WriteResponse>, Status> {
        let req = request.into_inner();
        
        // Convert protobuf Struct to serde_json::Value
        let value = prost_types_to_json(&req.value.unwrap_or_default());

        self.state_machine.write(
            &req.txn_id,
            req.namespace,
            req.agent_id,
            req.key,
            value,
        ).map_err(|e| Status::internal(format!("Write failed: {}", e)))?;

        Ok(Response::new(WriteResponse {}))
    }

    async fn delete(&self, request: Request<DeleteRequest>) -> Result<Response<DeleteResponse>, Status> {
        let req = request.into_inner();

        self.state_machine.delete(
            &req.txn_id,
            req.namespace,
            req.agent_id,
            req.key,
        ).map_err(|e| Status::internal(format!("Delete failed: {}", e)))?;

        Ok(Response::new(DeleteResponse {}))
    }

    async fn commit(&self, request: Request<CommitRequest>) -> Result<Response<CommitResponse>, Status> {
        let req = request.into_inner();

        let commit_ts = self.state_machine.commit(&req.txn_id)
            .map_err(|e| Status::internal(format!("Commit failed: {}", e)))?;

        Ok(Response::new(CommitResponse { commit_ts }))
    }

    async fn abort(&self, request: Request<AbortRequest>) -> Result<Response<AbortResponse>, Status> {
        let req = request.into_inner();

        self.state_machine.abort(&req.txn_id)
            .map_err(|e| Status::internal(format!("Abort failed: {}", e)))?;

        Ok(Response::new(AbortResponse {}))
    }

    async fn get_state(&self, request: Request<GetStateRequest>) -> Result<Response<GetStateResponse>, Status> {
        let req = request.into_inner();

        let state = self.state_machine.get_state(&req.namespace, &req.agent_id, &req.key)
            .map_err(|e| Status::internal(format!("GetState failed: {}", e)))?;

        if let Some(record) = state {
            let value = record.value.map(|v| json_to_prost_types(&v));
            Ok(Response::new(GetStateResponse {
                value,
                version: record.version,
                commit_ts: record.commit_ts,
                exists: !record.deleted,
            }))
        } else {
            Ok(Response::new(GetStateResponse {
                value: None,
                version: 0,
                commit_ts: 0,
                exists: false,
            }))
        }
    }

    async fn get_state_at_version(&self, request: Request<GetStateAtVersionRequest>) -> Result<Response<GetStateAtVersionResponse>, Status> {
        let req = request.into_inner();

        let state = self.state_machine.get_state_at_version(&req.namespace, &req.agent_id, &req.key, req.version)
            .map_err(|e| Status::internal(format!("GetStateAtVersion failed: {}", e)))?;

        if let Some(record) = state {
            let value = record.value.map(|v| json_to_prost_types(&v));
            Ok(Response::new(GetStateAtVersionResponse {
                value,
                version: record.version,
                commit_ts: record.commit_ts,
                exists: !record.deleted,
            }))
        } else {
            Ok(Response::new(GetStateAtVersionResponse {
                value: None,
                version: 0,
                commit_ts: 0,
                exists: false,
            }))
        }
    }

    async fn list_keys(&self, request: Request<ListKeysRequest>) -> Result<Response<ListKeysResponse>, Status> {
        let req = request.into_inner();

        let keys = self.state_machine.list_keys(&req.namespace, &req.agent_id)
            .map_err(|e| Status::internal(format!("ListKeys failed: {}", e)))?;

        Ok(Response::new(ListKeysResponse { keys }))
    }

    async fn scan_prefix(&self, request: Request<ScanPrefixRequest>) -> Result<Response<ScanPrefixResponse>, Status> {
        let req = request.into_inner();

        let records = self.state_machine.scan_prefix(&req.namespace, &req.agent_id, &req.prefix)
            .map_err(|e| Status::internal(format!("ScanPrefix failed: {}", e)))?;

        let entries = records.into_iter().map(|r| StateEntry {
            key: r.key,
            value: Some(json_to_prost_types(&r.value.unwrap_or_default())),
            version: r.version,
            commit_ts: r.commit_ts,
        }).collect();

        Ok(Response::new(ScanPrefixResponse { entries }))
    }

    type ReplayStream = ReceiverStream<Result<ReplayEvent, Status>>;

    async fn replay(&self, request: Request<ReplayRequest>) -> Result<Response<Self::ReplayStream>, Status> {
        let req = request.into_inner();

        let events = self.state_machine.replay(&req.namespace, &req.agent_id, req.start_ts, req.end_ts)
            .map_err(|e| Status::internal(format!("Replay failed: {}", e)))?;

        let (tx, rx) = tokio::sync::mpsc::channel(128);

        tokio::spawn(async move {
            for event in events {
                let operations = event.operations.into_iter().map(|op| Operation {
                    key: op.key,
                    value: op.value.map(|v| json_to_prost_types(&v)),
                    version: op.version,
                }).collect();

                let replay_event = ReplayEvent {
                    txn_id: event.txn_id,
                    commit_ts: event.commit_ts,
                    operations,
                };

                if tx.send(Ok(replay_event)).await.is_err() {
                    break;
                }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }
}

// Helper functions to convert between prost_types::Struct and serde_json::Value

fn prost_types_to_json(value: &prost_types::Struct) -> serde_json::Value {
    use prost_types::value::Kind;

    let map: serde_json::Map<String, serde_json::Value> = value.fields.iter().map(|(k, v)| {
        let json_val = match &v.kind {
            Some(Kind::NullValue(_)) => serde_json::Value::Null,
            Some(Kind::NumberValue(n)) => serde_json::json!(n),
            Some(Kind::StringValue(s)) => serde_json::json!(s),
            Some(Kind::BoolValue(b)) => serde_json::json!(b),
            Some(Kind::StructValue(s)) => prost_types_to_json(s),
            Some(Kind::ListValue(l)) => {
                let vals: Vec<serde_json::Value> = l.values.iter().map(|v| {
                    match &v.kind {
                        Some(Kind::NullValue(_)) => serde_json::Value::Null,
                        Some(Kind::NumberValue(n)) => serde_json::json!(n),
                        Some(Kind::StringValue(s)) => serde_json::json!(s),
                        Some(Kind::BoolValue(b)) => serde_json::json!(b),
                        _ => serde_json::Value::Null,
                    }
                }).collect();
                serde_json::Value::Array(vals)
            }
            None => serde_json::Value::Null,
        };
        (k.clone(), json_val)
    }).collect();

    serde_json::Value::Object(map)
}

fn json_to_prost_types(value: &serde_json::Value) -> prost_types::Struct {
    use prost_types::value::Kind;
    use std::collections::BTreeMap;

    let fields: BTreeMap<String, prost_types::Value> = match value {
        serde_json::Value::Object(map) => {
            map.iter().map(|(k, v)| {
                let kind = match v {
                    serde_json::Value::Null => Kind::NullValue(0),
                    serde_json::Value::Bool(b) => Kind::BoolValue(*b),
                    serde_json::Value::Number(n) => Kind::NumberValue(n.as_f64().unwrap_or(0.0)),
                    serde_json::Value::String(s) => Kind::StringValue(s.clone()),
                    serde_json::Value::Array(arr) => {
                        let values = arr.iter().map(|v| {
                            let kind = match v {
                                serde_json::Value::Null => Kind::NullValue(0),
                                serde_json::Value::Bool(b) => Kind::BoolValue(*b),
                                serde_json::Value::Number(n) => Kind::NumberValue(n.as_f64().unwrap_or(0.0)),
                                serde_json::Value::String(s) => Kind::StringValue(s.clone()),
                                _ => Kind::NullValue(0),
                            };
                            prost_types::Value { kind: Some(kind) }
                        }).collect();
                        Kind::ListValue(prost_types::ListValue { values })
                    }
                    serde_json::Value::Object(_) => Kind::StructValue(json_to_prost_types(v)),
                };
                (k.clone(), prost_types::Value { kind: Some(kind) })
            }).collect()
        }
        _ => BTreeMap::new(),
    };

    prost_types::Struct { fields }
}
