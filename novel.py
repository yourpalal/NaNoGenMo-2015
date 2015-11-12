import phrases
from conversation import *

import fileinput, math, random


def choose_with_probability(a, b, prob):
    """" chance of returning b is 0 <= prob <= 1 """
    if random.uniform(0, 1.0) <= prob:
        return  b
    return a

class UniformPicker(object):
    def __init__(self):
        self.chosen = None
        self.count = 0

    def add(self, pickable):
        self.count += 1

        if self.chosen is None:
            self.chosen = pickable
        else:
            # this is uniform
            # chance of keeping self.chosen = 1 - (1/n)
            self.chosen = choose_with_probability(self.chosen, pickable, 1.0 / self.count)
        return self.chosen == pickable

    def pick(self):
        return self.chosen


class Sentiment(object):
    def __init__(self, mocking = 0, confirming = 0, excitement = 0):
        self.mocking = mocking
        self.confirming = confirming
        self.excitement = excitement

    EXCITING_WORDS = ["!", "wow", "incredible", "amazing"]

    @staticmethod
    def for_phrase(phrase):
        lowered  = phrase.lower()

        score = Sentiment()
        score.excitement = sum(w in lowered for w in Sentiment.EXCITING_WORDS)

        return score

    @staticmethod
    def update_dialog_scores(dialog):
        for i in range(1, len(dialog)):
            current = dialog[i]
            previous = dialog[i - 1]
            last_by_actor = Sentiment.previous_phrase(dialog, i, current)
            last_by_actor = last_by_actor or DialoguePhrase("", phrases.FACT, current.actor)

            if Sentiment.is_mimicking(dialog, i):
                if last_by_actor.sentiment.mocking > 0:
                    current.sentiment.mocking = last_by_actor.sentiment.mocking + 1
                elif last_by_actor.sentiment.confirming > 0:
                    current.sentiment.confirming = last_by_actor.sentiment.confirming + 1
                elif random.uniform(0, 1) < 0.5:
                    current.sentiment.mocking += 1
                else:
                    current.sentiment.confirming += 1

    @staticmethod
    def is_mimicking(dialog, starting_from):
        words = dialog[starting_from].phrase
        actor = dialog[starting_from].actor

        for i in range(starting_from, max(0, starting_from - 9), - 1):
            if dialog[i].actor != actor and dialog[i].phrase == words:
                return True

    @staticmethod
    def previous_phrase(dialog, starting_from, actor):
        for i in range(starting_from, 0 , -1):
            if dialog[i].actor == actor:
                return dialog[i]
        return None

    def dist(self, other):
        return (self.excitement - other.excitement) ** 2 + \
            (self.mocking - other.mocking) ** 2 + \
            (self.confirming - other.confirming) ** 2

    def pick_direction(self):
        direction = ''
        score = 10000
        for d, s in Sentiment.DIRECTIONS.items():
            next_score = s.dist(self)
            if next_score == score:
                direction = random.choice([d, direction])
            elif next_score < score:
                score = next_score
                direction = d
        return direction

Sentiment.DIRECTIONS = {
    ' (mocking)': Sentiment(1, 0, 0),
    ' (mocking loudly)': Sentiment(2, 0, 0),
    ' (mocking excitedly)': Sentiment(1, 0, 1),
    ' (agreeing)': Sentiment(0, 1, 0),
    ' (cheering)': Sentiment(0, 1, 1),
    '': Sentiment(0, 0, 0)
}



class DialoguePhrase(object):
    def __init__(self, phrase, phrase_type, actor):
        self.phrase = phrase
        self.phrase_type = phrase_type
        self.actor = actor

        self.sentiment = Sentiment.for_phrase(phrase)

class Novel(object):
    def __init__(self):
        self.teacher = phrases.Corpus()
        add_teacher_conversation(self.teacher)

        self.student = phrases.Corpus()
        add_student_conversation(self.student)

        self.phrases = []

    def clean_corpuses(self):
        for corpus in (self.teacher, self.student):
            corpus.fix_casing()

            corpus.counts.delete("\\")
            corpus.counts.delete("\\\\")
            corpus.counts.delete("\\")
            corpus.counts.delete("\\1")

    def teach_teacher(self, document):
        self.teacher.add_document(document)

    def teach_student(self, document):
        self.student.add_document(document)

    def teacher_speak(self, phrase_type=None):
        phrase_type = phrase_type or self.randomPhraseType()

        phrase = self.teacher.generate_sentence(phrase_type)
        self.phrases.append(DialoguePhrase(phrase, phrase_type, "SOCRATES"))
        self.teach_student(phrase)

    def student_speak(self, phrase_type=None):
        phrase_type = phrase_type or self.randomPhraseType()

        phrase = self.student.generate_sentence(phrase_type)
        self.phrases.append(DialoguePhrase(phrase, phrase_type, "ARISTOTLE"))

        if phrase_type is phrases.FACT:
            self.teach_teacher(phrase)

    def student_discover(self, things=1):
        for i in range(things):
            self.teach_student(self.teacher.generate_sentence(phrases.DECLARATION))

    def randomPhraseType(self):
        return random.choice([phrases.FACT, phrases.DECLARATION, phrases.QUESTION])

    def compute_sentiments(self):
        Sentiment.update_dialog_scores(self.phrases)



if __name__ == '__main__':
    pickers = [UniformPicker() for i in range(8)]

    for l in fileinput.input():
        for p in pickers:
            p.add(l[:])

    novel = Novel()
    for p in pickers[:3]:
        # teach twice for higher probability of using this text
        novel.teach_teacher(p.chosen)
        novel.teach_teacher(p.chosen)

    for p in pickers[3:]:
        # teach twice for higher probability of using this text
        novel.teach_student(p.chosen)
        novel.teach_student(p.chosen)

    novel.clean_corpuses()

    for i in range(30):
        novel.teacher_speak(phrases.FACT)
        novel.teacher_speak(phrases.QUESTION)

        novel.student_speak()
        novel.student_discover(i)
        novel.student_speak(phrases.FACT)

    novel.compute_sentiments()

    for p in novel.phrases:
        direction = p.sentiment.pick_direction()
        print("{}{}: {}".format(p.actor, direction, p.phrase))
