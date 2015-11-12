import phrases

import itertools
from nose.tools import *


def test_simple_phrase():
    phrase = "Hey it works!"
    corpus = phrases.Corpus()
    corpus.add_sentence(phrase, phrases.DECLARATION)
    eq_(corpus.generate_sentence(phrases.DECLARATION), phrase)


def test_multiple_phrases():
    corpus = phrases.Corpus()
    corpus.add_sentences([
        "hey it works",
        "hey it made two sentences",
        "hey it works great",
        "it made something new",
    ])

    sentences = set(corpus.generate_sentence(phrases.DECLARATION) for i in range(10))
    print(sentences)

    ok_(len(sentences) >= 2, "should make multiple sentences, made {}".format(len(sentences)))


def test_delete():
    corpus = phrases.Corpus()
    corpus.add_sentences([
        "hey it works",
        "hey it made two sentences",
        "hey it works great",
        "it made something new",
    ])

    corpus.counts.delete("it")

    eq_(corpus.generate_sentence(phrases.DECLARATION), "Hey")

def test_fix_casing():
    corpus = phrases.Corpus()
    corpus.add_sentences([
        "Ringo is a Name",
        "name is not a Name"
    ])

    corpus.fix_casing()

    ok_(corpus.counts.has(["Ringo"]))
    ok_(not corpus.counts.has(["Name"]))
    ok_(not corpus.counts.has(["is", "a", "Name"]))
