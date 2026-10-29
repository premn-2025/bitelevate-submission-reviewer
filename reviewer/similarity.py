"""Overlap detection between submissions.

Two views of the code are compared:
  raw    - the token stream as written
  struct - the same stream with identifiers, strings and numbers masked, so a
           copy with renamed variables still lines up

A high score is a reason for a human to look, never a verdict.
"""
from __future__ import annotations

import io
import keyword
import re
import tokenize

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKIP = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER}


def code_views(py_texts: dict[str, str]) -> tuple[list[str], list[str]]:
    raw, struct = [], []
    for text in py_texts.values():
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type in SKIP:
                    continue
                raw.append(tok.string)
                if tok.type == tokenize.NAME:
                    struct.append(tok.string if keyword.iskeyword(tok.string) else "ID")
                elif tok.type == tokenize.NUMBER:
                    struct.append("NUM")
                elif tok.type == tokenize.STRING:
                    struct.append("STR")
                else:
                    struct.append(tok.string)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            continue
    return raw, struct


def _cosine(docs: list[str], ngram: tuple[int, int]) -> list[list[float]]:
    vec = TfidfVectorizer(token_pattern=r"\S+", ngram_range=ngram, sublinear_tf=True, lowercase=False)
    matrix = vec.fit_transform(docs)
    return cosine_similarity(matrix)


def readme_words(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def compare(target: dict, corpus: dict[str, dict], cfg: dict) -> list[dict]:
    """Compare one submission against a corpus.

    `target` and each corpus entry hold: raw (list), struct (list), readme (str).
    Returns matches sorted by strength, only those over the configured thresholds.
    """
    min_tokens = cfg["min_tokens"]
    matches = []
    if len(target["raw"]) < min_tokens:
        return matches
    names = [n for n, v in corpus.items() if len(v["raw"]) >= min_tokens]
    if not names:
        return matches
    raw_docs = [" ".join(target["raw"])] + [" ".join(corpus[n]["raw"]) for n in names]
    struct_docs = [" ".join(target["struct"])] + [" ".join(corpus[n]["struct"]) for n in names]
    raw_sim = _cosine(raw_docs, (3, 5))[0][1:]
    struct_sim = _cosine(struct_docs, (4, 6))[0][1:]
    read_sim = [0.0] * len(names)
    if len(target["readme"].split()) >= 40:
        # Short READMEs are left out of the comparison, not allowed to switch it off for everyone.
        long = [i for i, n in enumerate(names) if len(corpus[n]["readme"].split()) >= 40]
        if long:
            docs = [target["readme"]] + [corpus[names[i]]["readme"] for i in long]
            for i, sim in zip(long, _cosine(docs, (3, 3))[0][1:]):
                read_sim[i] = sim
    for i, name in enumerate(names):
        r, st, rd = float(raw_sim[i]), float(struct_sim[i]), float(read_sim[i])
        hit_code = st >= cfg["struct"] or r >= cfg["raw_only"]
        hit_readme = rd >= cfg["readme"]
        if hit_code or hit_readme:
            matches.append({
                "other": name,
                "raw": round(r, 2),
                "struct": round(st, 2),
                "readme": round(rd, 2),
                "reason": "code overlaps once names are masked" if hit_code else "README wording overlap",
            })
    return sorted(matches, key=lambda m: -(m["struct"] + m["raw"] + m["readme"]))
