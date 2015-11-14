import phrases, cleaners
from nose.tools import *

tokenize = phrases.Corpus.tokenize_sentence

def test_detetct_citations():
    # BEGIN WOW ( BOB 2890 ) END
    eq_(cleaners.detect_citations(tokenize("wow (Bob 2890)")), [(2,5)])

    eq_(cleaners.detect_citations(tokenize("wow (Bob 2890) neat (Jen 1800)")), [(7, 10), (2,5)])


def test_dont_fixer():
    eq_(cleaners.fix_bad_nt(["do", "n't"]), ["don't"])
    eq_(cleaners.fix_bad_nt(["have", "n't"]), ["haven't"])
    eq_(cleaners.fix_bad_nt(["is", "n't"]), ["isn't"])
    eq_(cleaners.fix_bad_nt(["would", "n't"]), ["wouldn't"])
    eq_(cleaners.fix_bad_nt(["should", "n't"]), ["shouldn't"])
    eq_(cleaners.fix_bad_nt(["wo", "n't"]), ["won't"])
    eq_(cleaners.fix_bad_nt(["does", "n't"]), ["doesn't"])
    eq_(cleaners.fix_bad_nt(["could", "n't"]), ["couldn't"])
    eq_(cleaners.fix_bad_nt(["are", "n't"]), ["aren't"])
    eq_(cleaners.fix_bad_nt(["need", "n't"]), ["needn't"])
    eq_(cleaners.fix_bad_nt(["were", "n't"]), ["weren't"])
    eq_(cleaners.fix_bad_nt(["did", "n't"]), ["didn't"])
    eq_(cleaners.fix_bad_nt(["had", "n't"]), ["hadn't"])
    eq_(cleaners.fix_bad_nt(["was", "n't"]), ["wasn't"])
    eq_(cleaners.fix_bad_nt(["ai", "n't"]), ["ain't"])
    eq_(cleaners.fix_bad_nt(["ca", "n't"]), ["can't"])

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
