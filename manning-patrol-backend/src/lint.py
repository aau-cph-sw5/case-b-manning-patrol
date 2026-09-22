"""Run linting: ruff + ty."""
import subprocess
import sys


def main():
    """Run ruff and ty checks."""
    # Run ruff
    ruff_result = subprocess.run(
        ["ruff", "check", "src/"],
        capture_output=True,
        text=True,
    )
    print(ruff_result.stdout)
    if ruff_result.returncode != 0:
        print(ruff_result.stderr)
        sys.exit(1)

    # Run ty
    ty_result = subprocess.run(
        ["ty", "check", "src/"],
        capture_output=True,
        text=True,
    )
    print(ty_result.stdout)
    if ty_result.returncode != 0:
        print(ty_result.stderr)
        sys.exit(1)

    print("All checks passed!")


if __name__ == "__main__":
    main()
