import phrases, cleaners
from nose.tools import *

tokenize = phrases.Corpus.tokenize_sentence

def test_detetct_citations():
    # BEGIN WOW ( BOB 2890 ) END
    eq_(cleaners.detect_citations(tokenize("wow (Bob 2890)")), [(2,5)])

    eq_(cleaners.detect_citations(tokenize("wow (Bob 2890) neat (Jen 1800)")), [(7, 10), (2,5)])


def test_dont_fixer():
    eq_(cleaners.swap_bad_tokens(["do", "n't"]), ["do", "not"])
    eq_(cleaners.swap_bad_tokens(tokenize("don't")), [0, "do", "not", -1])

def test_citation_replacer():
    eq_(cleaners.remove_citations(tokenize("wow (Bob 1995)")), [0, "wow", 2, -1])
    eq_(cleaners.remove_citations(tokenize("neat")), [0, "neat", -1])
    eq_(cleaners.remove_citations(tokenize("cool (oi b09b 1938) yay")), [0, "cool", 2, "yay", -1])

def test_tab_splitter():
    s = list(cleaners.tab_splitting_fixer(["this is one sentence", "this is another\tand so is this."]))
    eq_(len(s), 3)

    s = list(cleaners.tab_splitting_fixer(["this is one sentence", "this is another    and so is this."]))
    eq_(len(s), 2)

    s = list(cleaners.tab_splitting_fixer(["this is one sentence", "this is another          and so is this."]))
    eq_(len(s), 3)


def test_paren_remover():
    eq_(cleaners.remove_parens("wow neat".split()), "wow neat".split())
    eq_(cleaners.remove_parens("wow ( neat".split()), "wow neat".split())
    eq_(cleaners.remove_parens("wow ( ) { } neat".split()), "wow neat".split())

def test_number_remover():
    eq_(cleaners.remove_leading_numbers(tokenize("4.2 wow no numbers")), [0, "wow", "no", "numbers", -1])
