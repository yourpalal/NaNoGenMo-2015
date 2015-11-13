#!/usr/bin/env python3

from collections import defaultdict
import fileinput, itertools, math, nltk, random, re

from cleaners import *
from conversation import *

sentence_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

BEGIN = [0]
END = [-1]
EARLY_END = [-2]
CITATION = [2]

# basically an enum of phrase types. Some may be mutually exclusive, some may not.
QUESTION = 0
DECLARATION = 1
FACT = 2

FACT_WORDS = set(["hence", "therefore", "is", "can", "proven", "cannot", "must", "should"])

def lower(token):
    return token.lower() if hasattr(token, 'lower') else token

def islower(token):
    return token.islower() if hasattr(token, 'islower') else True


class GramNode(object):
    def __init__(self, parent):
        self.occurrences = defaultdict(lambda : 0)
        self.parent = parent
        self.children = defaultdict(self.make_child)

    def make_child(self):
        return GramNode(self)

    def add_occurrence(self, phrase_type):
        self.occurrences[phrase_type] += 1

    def likelihood(self, phrase_type):
        # take log of occurrences + 1 so that 0 occurrences = 0, and very common phrases
        # do not completely dominate our phrases
        return sum(map(lambda x: x.likelihood(phrase_type), self.children.values())) + math.log(self.occurrences[phrase_type] + 1)

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
        skip = random.random() * (self.likelihood(phrase_type) - math.log(self.occurrences[phrase_type] + 1))
        for token in self.children:
            skip -= self.children[token].likelihood(phrase_type)
            if skip <= 0:
                return token, self.children[token]

        return random.choice(list(self.children.items()) or [(EARLY_END[0], None)])

    def has(self, keys):
        if len(keys) == 0:
            return False
        elif len(keys) == 1:
            return keys[0] in self.children
        return keys[0] in self.children and self.children[keys[0]].has(keys[1:])

    def pick_best(self, keys, phrase_type):
        oldKeys = keys
        while (not self.has(keys)) and len(keys) > 0:
            keys = keys[1:]
        result = self.get(keys).pick(phrase_type)
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

    def show(self, spaces):
        for token, node in self.children.items():
            print("{}-> {}".format(spaces, token))
            node.show(spaces + "-")


PRE_PUNCT_SPACE_MATCHER = re.compile(r"\s+([.,:)}'?!]+)")
POST_PUNCT_SPACE_MATCHER = re.compile(r"([\({])\s+")


class Corpus(object):
    def __init__(self, gram_length=5):
        self.counts = GramNode(None)
        self.gram_length = gram_length

    @staticmethod
    def tokenize_sentence(sentence):
        return BEGIN + nltk.word_tokenize(sentence) + END

    @staticmethod
    def detokenize_sentence(sentence):
        result = " ".join(sentence)
        result = result[0].upper() + result[1:]
        result = PRE_PUNCT_SPACE_MATCHER.sub(r"\1", result)
        return POST_PUNCT_SPACE_MATCHER.sub(r"\1", result)

    @staticmethod
    def deduce_phrase_type(tokens):
        if tokens[-2] == "?" or tokens[-1] == "?": # -1 may be END
            return QUESTION
        if len(tokens) < 15 and FACT_WORDS.intersection(set(map(lambda t: lower(t), tokens))):
            return FACT
        return DECLARATION

    def add_document(self, doc):
        sentences = sentence_splitter.tokenize(doc)
        sentences = tab_splitting_fixer(sentences)
        sentences = abbrev_fixer(sentences)
        sentences = paren_matching_fixer(sentences)

        for s in sentences:
            tokens = self.tokenize_sentence(s)
            tokens = remove_citations(tokens)
            self.add_sentence(tokens)

    def add_sentence(self, tokens, phrase_type=None):
        if type(tokens) is str:
            tokens = self.tokenize_sentence(tokens)
        phrase_type = phrase_type or self.deduce_phrase_type(tokens)

        grams = list(nltk.ngrams(tokens, self.gram_length, pad_right=True, pad_symbol=None))
        for g in grams:
            if None in g:
                g = g[:g.index(None)]
                # we don't need the padding!
            self.counts.get(g).add_occurrence(phrase_type)

    def add_sentences(self, sentences, phrase_type=None):
        for s in sentences:
            self.add_sentence(s, phrase_type)

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
        while words[-1] != END[0] and words[-1] != EARLY_END[0]:
            # choose number of previous tokens to consider, trending towards more as our sentence grows
            context = self.gram_length - 1 - math.floor(random.random() ** math.log(len(words)) * (self.gram_length - 1))
            token, node = self.pick_next_token(words[-context:], phrase_type)
            words.append(token)
        words = self.replace_citation_special(words)
        return self.detokenize_sentence(words[2:-1]), words[-1] == END[0]

    def replace_citation_special(self, phrase):
        while CITATION[0] in phrase:
            at = phrase.index(CITATION[0])
            phrase = phrase[0:at] + ["(", "My", "Butt", "2034", ")"] + phrase[at + 1:]
        return phrase

    def word_set(self, node=None):
        node = node or self.counts
        all_words = set(node.children.keys()) - {BEGIN[0], END[0]} # strings only

        for child in node.children.values():
            all_words.update(self.word_set(child))
        return all_words

    def fix_casing(self):
        all_words = self.word_set()

        # if a word only shows up title cased, it is probably a name eg. Socrates
        no_lower = {lower(w) for w in all_words} - {w for w in all_words if islower(w)}
        self.to_lower(self.counts, no_lower)

    def to_lower(self, node, exempt):
        for child in node.children.values():
            self.to_lower(child, exempt)

        # make a list so that we don't get tripped up while deleting/adding keys
        for key in list(node.children.keys()):
            low_key = lower(key)
            if low_key in exempt or low_key == key:
                continue

            node.children[key].merge_into(node.children[low_key])
            del node.children[key]

    def show(self):
        self.counts.show("")


if __name__ == '__main__':
    corpus = Corpus()
    add_all_conversation(corpus)

    for l in fileinput.input():
        corpus.add_document(l)

    corpus.counts.delete("\\")
    corpus.counts.delete("\\\\")
    corpus.counts.delete("\\")
    corpus.counts.delete("\\1")

    corpus.fix_casing()


    for i in range(6):
        print("{}: {}".format(i, corpus.generate_sentence(i % 3)[0]))
