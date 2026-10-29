from scorer import Inquiry, tier, money_points, topic_points, rate_inquiry, time_points


def test_budget_tiers():
    assert money_points(600_000) == 30
    assert money_points(150_000) == 20
    assert money_points(25_000) == 10
    assert money_points(1_000) == 0


def test_keywords_are_case_insensitive():
    assert topic_points("Need CRM Automation") == 25


def test_no_keywords():
    assert topic_points("hello there") == 0


def test_urgency_short_timeline():
    assert time_points(2) == 15


def test_urgency_long_timeline():
    assert time_points(30) == 2


def test_score_is_capped():
    inquiry = Inquiry("Acme", 900_000, "automation agent crm cloud migration", 1)
    assert rate_inquiry(inquiry) == 100


def test_band_names():
    assert tier(60) == "hot"
    assert tier(30) == "warm"
    assert tier(5) == "cold"


def test_end_to_end_cold_lead():
    inquiry = Inquiry("Tiny", 1_000, "just browsing", 40)
    assert tier(rate_inquiry(inquiry)) == "cold"
