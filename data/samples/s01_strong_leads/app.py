"""Command line demo for the lead scorer."""
import sys

from scorer import Lead, band, score_lead


def main(argv: list[str]) -> None:
    """Score one lead given on the command line."""
    company, budget, weeks = argv[1], int(argv[2]), int(argv[3])
    lead = Lead(company, budget, " ".join(argv[4:]), weeks)
    value = score_lead(lead)
    print(f"{company}: {value} ({band(value)})")


if __name__ == "__main__":
    main(sys.argv)
