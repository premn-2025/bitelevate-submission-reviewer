from main import WordCounter


def test_counts():
    wc = WordCounter()
    wc.feed("a b a")
    assert wc.counts["a"] == 2


def test_stopwords():
    wc = WordCounter(stopwords=["a"])
    wc.feed("a b")
    assert "a" not in wc.counts
