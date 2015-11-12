import phrases

def add_all_conversation(corpus):
    add_teacher_conversation(corpus)
    add_only_student_conversation(corpus)

def add_student_conversation(corpus):
    add_common_conversation(corpus)
    add_only_student_conversation(corpus)

def add_only_student_conversation(corpus):
    corpus.add_prefixes([
        "I do not understand,",
        "It is understood,",
        "As I understand it,",
        "Of course,",
        "Agreed,"
    ], phrases.DECLARATION)

    corpus.add_suffixes([
        ", but then I'm lost",
        ", if I understand correctly",
        " EUREKA!",
    ], phrases.DECLARATION)

    corpus.add_sentences([
        "This is not correct.",
        "I disagree.",
    ])


def add_teacher_conversation(corpus):
    corpus.add_prefixes([
        "You do not understand,",
    ], phrases.DECLARATION)
    corpus.add_sentences([
        "I get the feeling that you do not understand the concept at hand.",
    ], phrases.DECLARATION)

    corpus.add_sentences([
        "This is not correct.",
        "I disagree.",
        "You must reconsider my earlier point.",
        "This is precisely the problem",
    ], phrases.FACT)

    corpus.add_sentences([
        "Have you considered"
    ], phrases.QUESTION)

def add_common_conversation(corpus):
    corpus.add_prefixes([
        "How does",
        "Could it be said",
        "Could it be said that",
        "Is it not the case",
        "Is it not the case that",
        "I wonder if",
    ], phrases.QUESTION)

    corpus.add_sentences([
        "can you believe it?"
    ], phrases.QUESTION)

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
    ], phrases.QUESTION)
