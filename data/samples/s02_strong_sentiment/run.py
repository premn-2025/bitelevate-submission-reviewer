"""Run the sentiment summary over a text file with one review per line."""
import sys
from pathlib import Path

from classifier import summarize


def load(path: str) -> list[str]:
    """Read non-empty lines from a file."""
    return [l.strip() for l in Path(path).read_text().splitlines() if l.strip()]


def main() -> None:
    """Print label counts for the file given as the first argument."""
    counts = summarize(load(sys.argv[1]))
    for name in ("positive", "neutral", "negative"):
        print(f"{name:<9} {counts.get(name, 0)}")


if __name__ == "__main__":
    main()
