"""Generate Python gRPC stubs from the .proto contract.

Outputs into `backend/src/` so modules import as `library.v1.<name>_pb2`.
Run:  python -m scripts.gen_proto
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
PROTO_DIR = REPO_ROOT / "proto"
OUT_DIR = BACKEND_DIR / "src"


def main() -> int:
    protos = sorted(PROTO_DIR.rglob("*.proto"))
    if not protos:
        print(f"No .proto files found under {PROTO_DIR}")
        return 1

    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I={PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        f"--pyi_out={OUT_DIR}",
        *[str(p) for p in protos],
    ]
    print("Generating stubs for:", ", ".join(p.name for p in protos))
    result = subprocess.run(cmd, check=False)
    if result.returncode == 0:
        print(f"Stubs written to {OUT_DIR / 'library' / 'v1'}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
