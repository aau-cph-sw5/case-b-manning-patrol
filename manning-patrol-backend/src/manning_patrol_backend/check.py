"""Run all CI checks locally before pushing."""

import subprocess
import sys

CHECKS = [
    ("Install dependencies", ["uv", "sync", "--locked"]),
    ("Lint", ["ruff", "check", "."]),
    ("Type check", ["ty", "check"]),
    ("Format check", ["ruff", "format", "--check"]),
    ("Tests", ["pytest"]),
]


def main():
    """Run the same steps as the backend CI workflow."""
    for name, command in CHECKS:
        print(f"==> {name}: {' '.join(command)}")
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"FAILED: {name} (exit code {result.returncode})")
            sys.exit(result.returncode)
    print("All checks passed!")


if __name__ == "__main__":
    main()
