#!/usr/bin/env python3

from collections import defaultdict
import fileinput, itertools, nltk, random, re

sentence_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

BEGIN = [0]
END = [-1]

# basically an enum of phrase types. Some may be mutually exclusive, some may not.
QUESTION = 0
DECLARATION = 1
FACT = 2

FACT_WORDS = set(["hence", "therefore", "is", "can", "cannot", "must", "should"])


class GramNode(object):
    def __init__(self, parent):
        self.occurrences = defaultdict(lambda : 0)
        self.parent = parent
        self.children = defaultdict(self.make_child)

    def make_child(self):
        return GramNode(self)

    def add_occurrence(self, phrase_type):
        self.occurrences[phrase_type] += 1

    def count(self, phrase_type):
        return sum(map(lambda x: x.count(phrase_type), self.children.values())) + self.occurrences[phrase_type]

    def get(self, keys):
        if len(keys) == 0:
            return self
        return self.children[keys[0]].get(keys[1:])

    def delete(self, key):
        if key in self.children:
            del self.children[key]
        for child in self.children.values():
            child.delete(key)

    def pick(self, phrase_type):
        skip = random.random() * self.count(phrase_type)
        for token in self.children:
            skip -= self.children[token].count(phrase_type)
            if skip <= 0:
                return token, self.children[token]
        return random.choice(self.children.items() or [(END[0], None)])

    def has(self, keys):
        return len(keys) == 0 or (keys[0] in self.children and self.children[keys[0]].has(keys[1:]))

    def pick_best(self, keys, phrase_type):
        oldKeys = keys
        while (not self.has(keys)) and len(keys) > 0:
            keys = keys[1:]
        result = self.get(keys).pick(phrase_type)
        # print("{} | {} -> {}".format(oldKeys, keys, result[0]))
        return result

    def merge_into(self, other, weight=1.0):
        for phrase_type, count in self.occurrences.items():
            other.occurrences[phrase_type ]+= count * weight
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

    @staticmethod
    def deduce_phrase_type(tokens):
        if tokens[-2] == "?" or tokens[-1] == "?": # -1 may be END
            return QUESTION
        if len(tokens) < 10 and FACT_WORDS.intersection(set(map(lambda t: str(t).lower(), tokens))):
            return FACT
        return DECLARATION

    def add_document(self, doc):
        for s in sentence_splitter.tokenize(doc):
            tokens = self.tokenize_sentence(s)
            self.add_sentence(tokens)

    def add_sentence(self, tokens, phrase_type=None):
        if type(tokens) is str:
            tokens = self.tokenize_sentence(tokens)
        phrase_type = phrase_type or self.deduce_phrase_type(tokens)

        grams = nltk.ngrams(tokens, 3)
        for g in grams:
            self.counts.get(g).add_occurrence(phrase_type)

    def add_prefixes(self, prefixes, phrase_type):
        for p in prefixes:
            tokens = self.tokenize_sentence(p)[:-1] # remove END token
            self.add_sentence(tokens, phrase_type)

    def add_suffixes(self, suffixes, phrase_type):
        for s in suffixes:
            tokens = self.tokenize_sentence(s)[1:] # remove BEGIN token
            self.add_sentence(tokens, phrase_type)

    def pick_next_token(self, previous, phrase_type):
        return self.counts.pick_best(previous, phrase_type)

    def generate_sentence(self, phrase_type):
        words = BEGIN + BEGIN
        while words[-1] != END[0]:
            token, node = self.pick_next_token(words[-2:], phrase_type)
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
        "How does",
    ], QUESTION)
    corpus.add_prefixes([
        "I get the feeling that you don't understand the concept at hand.",
        "You do not understand,",
        "I do not understand,",
        "It is understood,",
        "I understand,",
        "Of course,",
        "Agreed,"
    ], DECLARATION)
    corpus.add_suffixes([
        ", is that right?",
        ", or is it?",
        "or maybe not?",
    ], QUESTION)
    corpus.add_suffixes([
        ", but then I'm lost",
        ", if I understand correctly",
        " EUREKA!",
    ], DECLARATION)


    for l in fileinput.input():
        corpus.add_document(l)

    corpus.counts.delete("\\")
    corpus.counts.delete("\\\\")
    corpus.counts.delete("\\")
    corpus.counts.delete("\\1")

    corpus.fix_casing()

    for i in range(6):
        print("{}: {}".format(i, corpus.generate_sentence(i % 3)))
