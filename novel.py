import itertools, sys

from jinja2 import Environment, FileSystemLoader

from chapter import Chapter

def groupconsecutive(iter_in, *attrs):
    return itertools.groupby(iter_in, key=lambda x: [getattr(x, a) for a in attrs])

templates = Environment(loader=FileSystemLoader("./templates"))
templates.filters['groupconsecutive'] = groupconsecutive
novel_template = templates.get_template('novel.html')

class Novel(object):
    def __init__(self, chapters, title="Socrates and Aristotle are Fighting Again"):
        self.chapters = chapters
        self.title = title

    @staticmethod
    def create_from_corpus_file(filename, min_words=500):
        words = 0
        chapters = []

        while words < min_words:
            chapter = Chapter.create_from_corpus_file(filename)
            words += chapter.word_count
            print("generated chapter with {} words".format(chapter.word_count), file=sys.stderr)
            chapters.append(chapter)

        print("generated novel with {} chapters, {} words".format(len(chapters), words), file=sys.stderr)
        return Novel(chapters)


if __name__ == '__main__':
    corpus_filename = sys.argv[1]

    novel = Novel.create_from_corpus_file(corpus_filename, min_words=50000)
    print(novel_template.render(novel=novel))
