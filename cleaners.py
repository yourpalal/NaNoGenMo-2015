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


TAB_MATCHER = re.compile(r"\t|(\s\s\s\s\s\s+)")

def tab_splitting_fixer(phrases):
    """Splits sentences on tabs"""

    for p in phrases:
        for piece in TAB_MATCHER.split(p):
            if piece and not piece.isspace():
                yield piece

# these cleaners work on tokenized phrases, altering them in some way

def detect_citations(phrase, start_at=0):
    try:
        paren_start = phrase.index("(", start_at)
        paren_end = phrase.index(")", paren_start)
    except:
        return [] # no ( or )

    # potentially a bit too aggressive, but it's better to catch too many things
    # than to miss them
    for token in phrase[paren_start:paren_end]:
        if token.isdecimal():
            return detect_citations(phrase, paren_end) + [(paren_start, paren_end)]
    return detect_citations(phrase, paren_end)


def remove_citations(tokens):
    """Attempts to replace citations like (Ralph 2015) with the CITATION special
    token, to be replaced with another citation later."""

    if "(" in tokens and ")" in tokens:
        citations = detect_citations(tokens)
        for citation in detect_citations(tokens):
            tokens = tokens[0:citation[0]] + phrases.CITATION + tokens[citation[1] + 1:]

    return tokens

PARENS_TO_REMOVE = {"(", ")", "{", "}"}

def remove_parens(tokens):
    return [t for t in tokens if t not in PARENS_TO_REMOVE]
