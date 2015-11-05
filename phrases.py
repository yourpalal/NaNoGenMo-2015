#!/usr/bin/env python3

from collections import defaultdict
import fileinput, itertools, nltk, random, re

sentence_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

BEGIN = [0]
END = [-1]

class GramNode(object):
    def __init__(self, parent):
        self.occurrences = 0
        self.parent = parent
        self.children = defaultdict(self.make_child)

    def make_child(self):
        return GramNode(self)

    def add_occurrence(self):
        self.occurrences += 1

    def count(self):
        return sum(map(lambda x: x.count(), self.children.values())) + self.occurrences

    def get(self, keys):
        if len(keys) == 0:
            return self
        return self.children[keys[0]].get(keys[1:])

    def delete(self, key):
        if key in self.children:
            del self.children[key]
        for child in self.children.values():
            child.delete(key)

    def pick(self):
        skip = random.random() * self.count()
        for token in self.children:
            skip -= self.children[token].count()
            if skip <= 0:
                return token, self.children[token]
        return random.choice(self.children.items() or [(END[0], None)])

    def has(self, keys):
        return len(keys) == 0 or (keys[0] in self.children and self.children[keys[0]].has(keys[1:]))

    def pick_best(self, keys):
        oldKeys = keys
        while (not self.has(keys)) and len(keys) > 0:
            keys = keys[1:]
        result = self.get(keys).pick()
        # print("{} | {} -> {}".format(oldKeys, keys, result[0]))
        return result

    def merge_into(self, other, weight=1.0):
        other.occurrences += self.occurrences * weight
        for key in self.children:
            self.children[key].merge_into(other.children[key], weight)

    def traverse(self, f):
        for child in self.children.values():
            child.traverse(f)
        f(self)


PRE_PUNCT_SPACE_MATCHER = re.compile(r"\s+([.,:)}'?!]+)")
POST_PUNCT_SPACE_MATCHER = re.compile(r"([\({])\s+")


class Corpus(object):
    def __init__(self):
        self.counts = GramNode(None)

    @staticmethod
    def tokenize_sentence(sentence):
        return BEGIN + nltk.word_tokenize(sentence) + END

    @staticmethod
    def detokenize_sentence(sentence):
        result = " ".join(sentence)
        result = PRE_PUNCT_SPACE_MATCHER.sub(r"\1", result)
        return POST_PUNCT_SPACE_MATCHER.sub(r"\1", result)

    def add_document(self, doc):
        for s in sentence_splitter.tokenize(doc):
            tokens = self.tokenize_sentence(s)
            self.add_sentence(tokens)

    def add_sentence(self, tokens):
        if type(tokens) is str:
            tokens = self.tokenize_sentence(tokens)

        grams = nltk.ngrams(tokens, 3)
        for g in grams:
            self.counts.get(g).add_occurrence()

    def add_prefixes(self, prefixes):
        for p in prefixes:
            tokens = self.tokenize_sentence(p)[:-1] # remove END token
            self.add_sentence(tokens)

    def add_suffixes(self, suffixes):
        for s in suffixes:
            tokens = self.tokenize_sentence(s)[1:] # remove BEGIN token
            self.add_sentence(tokens)

    def pick_next_token(self, previous):
        return self.counts.pick_best(previous)

    def generate_sentence(self):
        words = BEGIN + BEGIN
        while words[-1] != END[0]:
            token, node = self.pick_next_token(words[-2:])
            words.append(token)
        return self.detokenize_sentence(words[2:-1])

    def word_set(self, node=None):
        node = node or self.counts
        all_words = set(node.children.keys()) - {BEGIN[0], END[0]} # strings only

        for child in node.children.values():
            all_words.update(self.word_set(child))
        return all_words

    def fix_casing(self):
        all_words = self.word_set()

        # if a word only shows up title cased, it is probably a name eg. Socrates
        no_lower = {w.lower() for w in all_words} - {w for w in all_words if w.islower()}
        self.to_lower(self.counts, no_lower)

        # make all sentences start with caps
        beginnings = self.counts.get(BEGIN)
        beginnings.children = {token.title(): child for (token, child) in beginnings.children.items()}

    def to_lower(self, node, exempt):
        for child in node.children.values():
            self.to_lower(child, exempt)

        # make a list so that we don't get tripped up while deleting/adding keys
        for key in list(node.children.keys()):
            lower = key.lower() if hasattr(key, 'lower') else key
            if lower in exempt or lower == key:
                continue

            node.children[key].merge_into(node.children[lower])
            del node.children[key]


if __name__ == '__main__':
    corpus = Corpus()

    corpus.add_prefixes([
        "I get the feeling that you don't understand the concept at hand.",
        "You do not understand,",
        "I do not understand,",
        "It is understood,",
        "I understand,",
        "Of course,",
        "Agreed,"
    ])
    corpus.add_suffixes([
        ", is that right?",
        ", but then I'm lost",
        ", if I understand correctly",
        " EUREKA!",
    ])


    for l in fileinput.input():
        corpus.add_document(l)

    corpus.counts.delete("\\")
    corpus.counts.delete("\\\\")
    corpus.counts.delete("\\")
    corpus.counts.delete("\\1")

    corpus.fix_casing()

    for i in range(5):
        print("{}: {}".format(i, corpus.generate_sentence()))
