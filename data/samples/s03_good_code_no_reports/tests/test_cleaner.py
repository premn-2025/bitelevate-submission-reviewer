from cleaner import dedupe, drop_empty, normalize_header, parse_number
from report import summary


def test_header_normalization():
    assert normalize_header("Total Amount (INR)") == "total_amount_inr"


def test_parse_plain_and_commas():
    assert parse_number("1,200.50") == 1200.5


def test_parse_parentheses_negative():
    assert parse_number("(45)") == -45


def test_parse_non_numeric():
    assert parse_number("abc") is None


def test_drop_empty_rows():
    assert drop_empty([{"a": ""}, {"a": "x"}]) == [{"a": "x"}]


def test_dedupe_keeps_first():
    rows = [{"id": "1", "v": "a"}, {"id": "1", "v": "b"}]
    assert dedupe(rows, "id") == [{"id": "1", "v": "a"}]


def test_summary_line():
    assert "2 removed" in summary(10, 8)
