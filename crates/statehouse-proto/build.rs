fn main() -> Result<(), Box<dyn std::error::Error>> {
    let manifest_dir = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR")?);
    let proto_file = manifest_dir.join("proto/statehouse/v1/statehouse.proto");
    let proto_include = manifest_dir.join("proto");
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile_protos(&[proto_file], &[proto_include])?;
    Ok(())
}
