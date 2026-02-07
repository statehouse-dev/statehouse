#!/usr/bin/env bash
set -euo pipefail

# Generate Python protobuf and gRPC stubs from proto files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_DIR="$SCRIPT_DIR/../proto"
PYTHON_DIR="$SCRIPT_DIR/statehouse/_generated"

echo "Generating Python gRPC stubs..."

# Create output directory
mkdir -p "$PYTHON_DIR"

# Generate protobuf and gRPC code
python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$PYTHON_DIR" \
    --grpc_python_out="$PYTHON_DIR" \
    --pyi_out="$PYTHON_DIR" \
    "$PROTO_DIR/statehouse/v1/statehouse.proto"

# Fix imports in generated files (grpc_tools generates incorrect relative imports)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/from statehouse\.v1 import statehouse_pb2/from . import statehouse_pb2/' "$PYTHON_DIR/statehouse/v1/statehouse_pb2_grpc.py"
else
    sed -i 's/from statehouse\.v1 import statehouse_pb2/from . import statehouse_pb2/' "$PYTHON_DIR/statehouse/v1/statehouse_pb2_grpc.py"
fi

# Create __init__.py files
touch "$PYTHON_DIR/__init__.py"
touch "$PYTHON_DIR/statehouse/__init__.py"
touch "$PYTHON_DIR/statehouse/v1/__init__.py"

echo "✅ Generated Python stubs in $PYTHON_DIR"
