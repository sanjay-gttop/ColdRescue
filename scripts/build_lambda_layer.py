"""
Build Lambda runtime dependencies layer (Linux Python 3.12 x86_64).
Downloads wheels into infrastructure/layers/runtime/python.
"""
import subprocess
import sys
from pathlib import Path

def build_layer():
    root = Path(__file__).parent.parent
    target_dir = root / "infrastructure" / "layers" / "runtime" / "python"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--platform",
        "manylinux2014_x86_64",
        "--target",
        str(target_dir),
        "--only-binary=:all:",
        "--implementation",
        "cp",
        "--python-version",
        "312",
        "pydantic",
    ]
    print(f"Installing dependencies to {target_dir}...")
    subprocess.check_call(cmd)
    print("Lambda runtime layer built successfully.")

if __name__ == "__main__":
    build_layer()
