import phrases
from conversation import *

import fileinput, math, random


def choose_with_probability(a, b, prob):
    """" chance of returning b is 0 <= prob <= 1 """
    if random.uniform(0, 1.0) <= prob:
        return  b
    return a

class UniformPicker:
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


class Novel(object):
    def __init__(self):
        self.teacher = phrases.Corpus()
        add_teacher_conversation(self.teacher)

        self.student = phrases.Corpus()
        add_student_conversation(self.student)

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
        print("TEACHER: {}".format(phrase))

        self.teach_student(phrase)

    def student_speak(self, phrase_type=None):
        phrase_type = phrase_type or self.randomPhraseType()

        phrase = self.teacher.generate_sentence(phrase_type)
        print("STUDENT: {}".format(phrase))

        if phrase_type is phrases.FACT:
            self.teach_teacher(phrase)

    def student_discover(self, things=1):
        for i in range(things):
            self.teach_student(self.teacher.generate_sentence(phrases.DECLARATION))

    def randomPhraseType(self):
        return random.choice([phrases.FACT, phrases.DECLARATION, phrases.QUESTION])



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
        novel.student_discover(math.ceil(i / 5))
        novel.student_speak(phrases.FACT)
