import phrases

import itertools
from nose.tools import *


def test_simple_phrase():
    phrase = "Hey it works!"
    corpus = phrases.Corpus()
    corpus.add_sentence(phrase, phrases.DECLARATION)
    generated = corpus.generate_sentence(phrases.DECLARATION)
    eq_(generated.detokenized, phrase)
    eq_(generated.interrupted, False)


def test_multiple_phrases():
    corpus = phrases.Corpus()
    corpus.add_sentences([
        "hey it works",
        "hey it made two sentences",
        "hey it works great",
        "it made something new",
    ])

    sentences = set(corpus.generate_sentence(phrases.DECLARATION).detokenized for i in range(10))
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

    generated = corpus.generate_sentence(phrases.DECLARATION)
    eq_(generated.detokenized, "Hey")
    eq_(generated.interrupted, True)

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

def test_splits_sentences_on_tabs():
    corpus = phrases.Corpus()
    corpus.add_document("this is a thing\tand this is another thing")

    ok_(corpus.counts.has("this is a".split()))
    ok_(not corpus.counts.has("thing and this".split()))
