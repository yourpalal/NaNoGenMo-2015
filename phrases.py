#!/usr/bin/env python3

from collections import defaultdict
import fileinput, itertools, nltk, random, re

sentence_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

BEGIN = [0]
END = [-1]

class GramNode(object):
    def __init__(self, parent):
        self.sentences = []
        self.parent = parent
        self.children = defaultdict(self.make_child)

    def make_child(self):
        return GramNode(self)

    def add_sentence(self, sentence):
        self.sentences.append(sentence)

    def count(self):
        return sum(map(lambda x: x.count(), self.children.values())) + len(self.sentences)

    def get(self, keys):
        if len(keys) == 0:
            return self
        return self.children[keys[0]].get(keys[1:])

    def pick(self):
        skip = random.random() * self.count()
        for token in self.children:
            skip -= self.children[token].count()
            if skip <= 0:
                return token, self.children[token]
        return random.choice(self.children.items() or [(END, None)])

    def has(self, keys):
        return len(keys) == 0 or (keys[0] in self.children and self.children[keys[0]].has(keys[1:]))

    def pick_best(self, keys):
        oldKeys = keys
        while (not self.has(keys)) and len(keys) > 0:
            keys = keys[1:]
        result = self.get(keys).pick()
        print("{} | {} -> {}".format(oldKeys, keys, result[0]))
        return result


def tokenize_sentence(sentence):
    return BEGIN + nltk.word_tokenize(sentence) + END

SPACE_PUNCT_MATCHER = re.compile(r"\s+([.,(){}'?!]+)")

def detokenize_sentence(sentence):
    result = " ".join(sentence)
    return SPACE_PUNCT_MATCHER.sub(r"\1", result)


if __name__ == '__main__':
    sentences = (sentence_splitter.tokenize(l) for l in fileinput.input())
    specials = [
        "I get the feeling that you don't understand the concept at hand.",
        "You do not understand.",
        "I do not understand.",
        "It is understood.",
        "Could you expand on that?",
        "Of course.",
        "Not quite.",
        "And then?",
        "So what?",
        "Yes, exactly!",
        "You are getting closer.",
        "The problem is unclear.",
        "The problem is obvious."
    ]
    phrases = (tokenize_sentence(s) for s in itertools.chain.from_iterable(sentences))
    phrases = itertools.chain(phrases, iter(specials))
    three_grams = (nltk.ngrams(p, 3) for p in phrases)

    counts = GramNode(None)

    for gram in itertools.chain.from_iterable(three_grams):
        counts.get(gram).add_sentence(three_grams)

    words = BEGIN + BEGIN

    while words[-1] != END[0]:
        token, node = counts.pick_best(words[-2:])
        words.append(token)

    print(detokenize_sentence(words[2:-1]))
