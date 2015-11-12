import phrases, cleaners
from nose.tools import *

tokenize = phrases.Corpus.tokenize_sentence

def test_detetct_citations():
    # BEGIN WOW ( BOB 2890 ) END
    eq_(cleaners.detect_citations(tokenize("wow (Bob 2890)")), [(2,5)])

    eq_(cleaners.detect_citations(tokenize("wow (Bob 2890) neat (Jen 1800)")), [(7, 10), (2,5)])


def test_citation_replacer():
    eq_(cleaners.remove_citations(tokenize("wow (Bob 1995)")), [0, "wow", 2, -1])
    eq_(cleaners.remove_citations(tokenize("neat")), [0, "neat", -1])
    eq_(cleaners.remove_citations(tokenize("cool (oi b09b 1938) yay")), [0, "cool", 2, "yay", -1])
