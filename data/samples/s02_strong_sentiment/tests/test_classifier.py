from classifier import label, polarity, summarize, tokenize


def test_tokenize_lowercases():
    assert tokenize("Great Service") == ["great", "service"]


def test_positive_label():
    assert label("fast and helpful") == "positive"


def test_negative_label():
    assert label("slow and rude") == "negative"


def test_negation_flips_sign():
    assert polarity(tokenize("not great")) == -1


def test_neutral_label():
    assert label("the box arrived") == "neutral"


def test_summarize_counts():
    counts = summarize(["love it", "terrible", "ok"])
    assert counts["positive"] == 1 and counts["negative"] == 1 and counts["neutral"] == 1
