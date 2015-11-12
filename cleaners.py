import phrases

import re

# these cleaners work with phrses in string form. They fix improper sentence
# splitting.
def paren_count(phrase):
    """phrase is expected to be a string"""
    opened = 0
    for char in phrase:
        if char == "(":
            opened += 1
        elif char == ")":
            opened -= 1
        if opened < 0: # closing parens before opening
            return opened
    return opened

def paren_matching_fixer(phrases):
    """Takes an iterator of phrases, and stitches two together when a
    sentence is incorrectly broken in between ( and ) """
    broken = []
    count = 0
    for p in phrases:
        count += paren_count(p)

        if count > 0:
            broken.append(p)
            continue
        elif broken:
            broken.append(p)
            p = "".join(broken)
        broken = []
        count = 0
        yield p


ABBREV_MATCHERS = (
    re.compile(r"et al ?\.\s*$"), # match et al .
    re.compile(r"pp\.\s*$"),  # match pp.
    re.compile(r"e\.?g\.\s*$"), # match e.g.
    re.compile(r"cf\.\s*$") # match e.g.
)

def abbrev_fixer(phrases):
    """Takes an iterator of phrases, and stitches two together when a
    sentence is incorrectly broken on "et al." """
    broken = []
    for p in phrases:
        if any(matcher.search(p) for matcher in ABBREV_MATCHERS):
            broken.append(p)
            continue
        if broken:
            broken.append(p)
            yield "".join(broken)
            broken = []
        yield p


# these cleaners work on tokenized phrases, altering them in some way

def detect_citations(phrase, start_at=0):
    try:
        paren_start = phrase.index("(", start_at)
        paren_end = phrase.index(")", paren_start)
    except:
        return [] # no ( or )

    # too long to be a citation
    if paren_end - paren_start > 10:
        return detect_citations(paren_end)

    try:
        yearOrPage = int(phrase[paren_end - 1])
        return detect_citations(phrase, paren_end) + [(paren_start, paren_end)]
    except:
        return detect_citations(phrase, paren_end)


def remove_citations(tokens):
    """Attempts to replace citations like (Ralph 2015) with the CITATION special
    token, to be replaced with another citation later."""

    if "(" in tokens and ")" in tokens:
        citations = detect_citations(tokens)
        for citation in detect_citations(tokens):
            tokens = tokens[0:citation[0]] + phrases.CITATION + tokens[citation[1] + 1:]

    return tokens
