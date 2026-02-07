// Statehouse Daemon
// gRPC server implementation

mod service;

use anyhow::Result;
use std::sync::Arc;
use tonic::transport::Server;
use tracing::info;

use statehouse_core::{
    state_machine::StateMachine,
    storage::{InMemoryStorage, RocksStorage, StorageConfig},
};
use statehouse_proto::statehouse_service_server::StatehouseServiceServer;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    // Startup banner
    print_startup_banner();

    // Initialize storage
    let use_memory = std::env::var("STATEHOUSE_USE_MEMORY").is_ok();
    let storage: Arc<dyn statehouse_core::storage::Storage> = if use_memory {
        info!("📦 Storage: In-memory (ephemeral)");
        Arc::new(InMemoryStorage::new())
    } else {
        let config = StorageConfig::default();
        info!("📦 Storage: RocksDB");
        info!("📁 Data directory: {:?}", config.data_dir);
        Arc::new(RocksStorage::new(config)?)
    };

    // Initialize state machine
    let state_machine = Arc::new(StateMachine::new(storage));

    // Create gRPC service
    let service = service::StatehouseServiceImpl::new(state_machine.clone());

    // Server address
    let addr = std::env::var("STATEHOUSE_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:50051".to_string())
        .parse()?;

    info!("✅ Statehouse daemon ready");
    info!("📡 Listening on {}", addr);
    info!("");
    info!("💡 Tip: Use RUST_LOG=debug for verbose logging");
    info!("");

    // Start gRPC server
    Server::builder()
        .add_service(StatehouseServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}

fn print_startup_banner() {
    let version = env!("CARGO_PKG_VERSION");
    let git_sha = option_env!("GIT_SHA").unwrap_or("dev");
    
    println!();
    println!("╔════════════════════════════════════════════════╗");
    println!("║                                                ║");
    println!("║          🏛️  STATEHOUSE DAEMON 🏛️             ║");
    println!("║                                                ║");
    println!("║     Strongly consistent state + memory         ║");
    println!("║            engine for AI agents                ║");
    println!("║                                                ║");
    println!("╚════════════════════════════════════════════════╝");
    println!();
    info!("🔖 Version: {} ({})", version, git_sha);
    info!("🦀 Rust runtime initialized");
    println!();
}

