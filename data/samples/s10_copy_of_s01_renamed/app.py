"""Command line demo for the inquiry scorer."""
import sys

from scorer import Inquiry, tier, rate_inquiry


def main(argv: list[str]) -> None:
    """Score one inquiry given on the command line."""
    client, budget, weeks = argv[1], int(argv[2]), int(argv[3])
    inquiry = Inquiry(client, budget, " ".join(argv[4:]), weeks)
    result = rate_inquiry(inquiry)
    print(f"{client}: {result} ({tier(result)})")


if __name__ == "__main__":
    main(sys.argv)
