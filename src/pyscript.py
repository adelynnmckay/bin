#!/usr/bin/env python3

import os
import sys
import hashlib
import venv
import subprocess
import shlex
from pathlib import Path

def parse_reqs(script_path: Path) -> list[str]:
    with open(script_path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("# requirements:"):
                return shlex.split(line.partition(":")[2].strip())
    return []

def get_venv_path(script_path: Path, deps: list[str]) -> Path:
    h = hashlib.sha256(" ".join(deps).encode()).hexdigest()[:12]
    return Path.home() / ".cache" / f"pyscript-{script_path.stem}-{h}"

def create_venv(venv_path: Path):
    print(f"🔧 Creating venv at {venv_path}")
    venv.EnvBuilder(with_pip=True).create(venv_path)

def install_deps(python_path: Path, deps: list[str]):
    subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python_path, "-m", "pip", "install", *deps])

def exec_in_venv(python_path: Path, script: Path, args: list[str]):
    env = os.environ.copy()
    env["PYSCRIPT_ACTIVE"] = "1"
    os.execve(str(python_path), [str(python_path), str(script), *args], env)

def main():
    if os.environ.get("PYSCRIPT_ACTIVE") == "1":
        return

    if len(sys.argv) < 2:
        print("Usage: pyscript <your-script.py> [args...]")
        sys.exit(1)

    script = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    deps = parse_reqs(script)

    venv_path = get_venv_path(script, deps)
    python_bin = venv_path / "bin" / "python"

    if not python_bin.exists():
        create_venv(venv_path)
        install_deps(python_bin, deps)

    exec_in_venv(python_bin, script, args)

if __name__ == "__main__":
    main()
