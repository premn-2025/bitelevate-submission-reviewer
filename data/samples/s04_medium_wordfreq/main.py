"""Count word frequencies in a text file."""
import argparse
import re
from collections import Counter


class WordCounter:
    """Keeps running word counts."""

    def __init__(self, stopwords=None):
        self.counts = Counter()
        self.stopwords = set(stopwords or [])

    def feed(self, text):
        words = re.findall(r"[a-zA-Z']+", text.lower())
        for w in words:
            if w not in self.stopwords:
                self.counts[w] += 1

    def top(self, n=10):
        """Most common n words."""
        return self.counts.most_common(n)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    wc = WordCounter(stopwords=["the", "a", "of", "and"])
    with open(args.path) as fh:
        for line in fh:
            wc.feed(line)
    for word, n in wc.top(args.top):
        print(word, n)


if __name__ == "__main__":
    main()
