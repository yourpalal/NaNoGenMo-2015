#!/usr/bin/env python3

from collections import defaultdict
import fileinput, itertools, math, nltk, random, re

sentence_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

BEGIN = [0]
END = [-1]
CITATION = [2]

# basically an enum of phrase types. Some may be mutually exclusive, some may not.
QUESTION = 0
DECLARATION = 1
FACT = 2

FACT_WORDS = set(["hence", "therefore", "is", "can", "cannot", "must", "should"])

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

        return random.choice(list(self.children.items()) or [(END[0], None)])

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

def paren_count(phrase):
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


def detect_citations(phrase, start_at=0):
    try:
        paren_start = phrase.index("(", start_at)
        paren_end = phrase.index(")", paren_start)
    except:
        return [] # no ( or )

    # too long to be a citation
    if paren_end - paren_start > 10:
        return detect_citations(paren_end)

    try:
        yearOrPage = int(phrase[paren_end - 1])
        return detect_citations(phrase, paren_end) + [(paren_start, paren_end)]
    except:
        return detect_citations(phrase, paren_end)


def remove_citations(tokens):
    """Attempts to replace citations like (Ralph 2015) with the CITATION special
    token, to be replaced with another citation later."""

    if "(" in tokens and ")" in tokens:
        citations = detect_citations(tokens)
        for citation in detect_citations(tokens):
            tokens = tokens[0:citation[0]] + CITATION + tokens[citation[1] + 1:]

    return tokens


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
        if len(tokens) < 10 and FACT_WORDS.intersection(set(map(lambda t: lower(t), tokens))):
            return FACT
        return DECLARATION

    def add_document(self, doc):
        sentences = sentence_splitter.tokenize(doc)
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
        while words[-1] != END[0]:
            # choose number of previous tokens to consider, trending towards more as our sentence grows
            context = self.gram_length - 1 - math.floor(random.random() ** math.log(len(words)) * (self.gram_length - 1))
            token, node = self.pick_next_token(words[-context:], phrase_type)
            words.append(token)
        words = self.replace_citation_special(words)
        return self.detokenize_sentence(words[2:-1])

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

    corpus.add_prefixes([
        "You do not understand,",
        "I do not understand,",
        "It is understood,",
        "As I understand it,",
        "Of course,",
        "Agreed,"
    ], DECLARATION)
    corpus.add_sentences([
        "I get the feeling that you do not understand the concept at hand.",
    ], DECLARATION)
    corpus.add_suffixes([
        ", but then I'm lost",
        ", if I understand correctly",
        " EUREKA!",
    ], DECLARATION)

    corpus.add_sentences([
        "This is not correct.",
        "I disagree.",
        "You must reconsider my earlier point.",
        "This is precisely the problem",
    ], FACT)

    corpus.add_prefixes([
        "How does",
        "Could it be said",
        "Could it be said that",
        "Is it not the case",
        "Is it not the case that",
        "I wonder if",
        "Have you considered"
    ], QUESTION)
    corpus.add_sentences([
        "can you believe it?"
    ], QUESTION)
    corpus.add_suffixes([
        "case at hand?",
        "case in question?",
        "that is true?",
        "that is false?",
        "that is consistent?",
        "that is inconsistent?",
        ", is that right?",
        ", or is it?",
        "or maybe not?",
    ], QUESTION)



    for l in fileinput.input():
        corpus.add_document(l)

    corpus.counts.delete("\\")
    corpus.counts.delete("\\\\")
    corpus.counts.delete("\\")
    corpus.counts.delete("\\1")

    corpus.fix_casing()


    for i in range(6):
        print("{}: {}".format(i, corpus.generate_sentence(i % 3)))
