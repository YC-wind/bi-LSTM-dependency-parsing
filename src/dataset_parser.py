import numpy as np
import re


class DatasetParser:

    def __init__(self, sentence, word2vec):
        sentence = [['0', '<ROOT/>', '_', 'ROOT', '_', '_', '_', '_', '_', '_']]\
                   + sentence\
                   + [['-1', '<EMPTY/>', '_', 'EMPTY', '_', '_', '_', '_', '_', '_']]
        arr = np.array(np.array(sentence)[:, (0, 1, 3, 6, 7)])
        self.__buffer = arr.tolist()
        self.__stack = []
        self.__dependencies = [sum([e == str(i) for e in arr[:, 3]]) for i in range(arr.shape[0])]
        self.__sentence = sentence
        self.__word2vec = word2vec

        self.__shift()
        self.__shift()

    def sentence2couples(self):
        return [[int(w[6]), i + 1, w[7]] for i, w in enumerate(self.__sentence[1:-1])]

    def sentence2couples_parent(self):
        sentence = [['0', '<ROOT/>', '_', 'ROOT', '_', '_', '0', '_', '_', '_']] + self.__sentence[1:-1]
        return [[int(sentence[int(w[6])][6]), int(w[6]), i, w[7]] for i, w in enumerate(sentence)]

    def index2mask(self, index):
        mask = np.zeros(len(self.__sentence), dtype=bool)
        mask[index] = True
        return mask

    def decompose_word(self, word):
        splitted = re.split('[^A-Za-z]*', word)

        new_value = np.zeros((300,))
        for component in splitted:
            if component and component in self.__word2vec:
                new_value += self.__word2vec[component] / np.linalg.norm(self.__word2vec[component])

        return new_value / np.linalg.norm(new_value) if np.linalg.norm(new_value) != 0 else self.__word2vec['<UNK/>']

    def sentence2vec(self):
        vector_list = []
        for word in self.__sentence:
            if word[1] in self.__word2vec:
                vector_list.append(self.__word2vec[word[1]])
            else:
                vector_list.append(self.decompose_word(word[1]))

        vector_list[0] = self.__word2vec['.']
        return np.array(vector_list)

    def __shift(self):
        self.__stack.append(self.__buffer.pop(0))
        return 'shift'

    def __reduce_right(self, label=None):
        self.__dependencies[int(self.__stack[-2][0])] -= 1
        return 'reduce-right-' + (self.__stack.pop(-1)[4] if label is None else label)

    def __reduce_left(self, label=None):
        self.__dependencies[int(self.__stack[-1][0])] -= 1
        return 'reduce-left-' + (self.__stack.pop(-2)[4] if label is None else label)

    def has_next(self):
        return bool(self.__buffer[0] != ['-1', '<EMPTY/>', 'EMPTY', '_', '_']
                    or self.__stack[-1] != ['0', '<ROOT/>', 'ROOT', '_', '_'])

    def next(self, action=None, label=None):
        if action is None:
            if self.__stack[-1][3] == self.__stack[-2][0] and self.__dependencies[int(self.__stack[-1][0])] == 0:
                return self.__reduce_right()
            elif self.__stack[-2][3] == self.__stack[-1][0] and self.__dependencies[int(self.__stack[-2][0])] == 0:
                return self.__reduce_left()
            else:
                return self.__shift()
        else:
            if label is None:
                label = (None, None)

            for a in action:
                if a == 'reduce-right' and len(self.__stack) > 2:
                    return self.__reduce_right(label[1])
                elif a == 'reduce-right' and self.__buffer[0] == ['-1', '<EMPTY/>', 'EMPTY', '_', '_']:
                    return self.__reduce_right(label[1])
                elif a == 'reduce-left' and len(self.__stack) > 2:
                    return self.__reduce_left(label[0])
                elif a == 'shift' and self.__buffer[0] != ['-1', '<EMPTY/>', 'EMPTY', '_', '_']:
                    return self.__shift()

    def get_stack(self):
        return int(self.__stack[-1][0]), int(self.__stack[-2][0])

    def get_buffer(self):
        return int(self.__buffer[0][0])
