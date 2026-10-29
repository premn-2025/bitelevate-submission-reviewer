from scorer import Lead, band, budget_points, keyword_points, score_lead, urgency_points


def test_budget_tiers():
    assert budget_points(600_000) == 30
    assert budget_points(150_000) == 20
    assert budget_points(25_000) == 10
    assert budget_points(1_000) == 0


def test_keywords_are_case_insensitive():
    assert keyword_points("Need CRM Automation") == 25


def test_no_keywords():
    assert keyword_points("hello there") == 0


def test_urgency_short_timeline():
    assert urgency_points(2) == 15


def test_urgency_long_timeline():
    assert urgency_points(30) == 2


def test_score_is_capped():
    lead = Lead("Acme", 900_000, "automation agent crm cloud migration", 1)
    assert score_lead(lead) == 100


def test_band_names():
    assert band(60) == "hot"
    assert band(30) == "warm"
    assert band(5) == "cold"


def test_end_to_end_cold_lead():
    lead = Lead("Tiny", 1_000, "just browsing", 40)
    assert band(score_lead(lead)) == "cold"
