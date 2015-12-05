
from pprint import pprint
import random
import re
import sys

__author__ = 'iped'



class BagelAI:

    FULL_DICTIONARY_FILE = 'full_dictionary.txt'
    SHORT_DICTIONARY_FILE = 'common_dictionary.txt'

    def __init__(self, difficulty):
        """
        Initializes BagelGame class
        """
        self._short_dict = \
            self._read_five_letter_words(self.SHORT_DICTIONARY_FILE)
        self._full_dict = \
            self._read_five_letter_words(self.FULL_DICTIONARY_FILE)
        self._secret_word = ''
        self._possible_words = self._full_dict
        self._guesses = {}
        self._all_combos_not_in = {}
        self._all_combos_or_in = {}
        self._difficulty = difficulty

    @property
    def secret_word(self):
        return self._secret_word

    def is_secret_word(self, word):
        return word == self._secret_word

    def in_full_dict(self, word):
        return word in self._full_dict

    def are_words_remaining(self):
        return len(self._possible_words) > 0

    def _calculate_combos(self, guess, num):
        """
        Updates rules for exclusion
        :returns: not_in, or_in
        """
        return self._letter_combos(guess, num+1), \
            self._letter_combos(guess, num)

    def _calculate_and_store_combos(self, guess, num):
        not_in, or_in = self._calculate_combos(guess, num)
        self._all_combos_not_in[not_in] = (guess, num)
        self._all_combos_or_in[or_in] = (guess, num)
        return not_in, or_in

    @staticmethod
    def _read_five_letter_words(dictionary_file):
        """
        Returns a list of all five letter words
        """
        return [x.strip().lower() for x in
                open(dictionary_file).readlines()
                if len(x.strip().lower()) == 5]

    @staticmethod
    def _letter_combos(word, length, start=0):
        """
        Returns all of the possible combinations of "length" letters
        that are present in "word", starting at position "start"
        """
        combos = []
        # letters = list(word)
        if length == 1:
            return tuple([(x,) for x in word[start:]])
        for i in range(start, len(word)):
            this_letter = word[i]
            other_letters = BagelAI._letter_combos(word, length-1, i+1)
            for other_letter in other_letters:
                all_letters = list(this_letter)
                all_letters.extend(other_letter)
                combos.append(tuple(all_letters))
        return tuple(combos)

    def choose_new_word(self):
        """
        Chooses a new word for the computer
        """
        self._secret_word = \
            random.choice(self._short_dict)

    @staticmethod
    def _combo_in_word(combo, word):
        """
        :return: True if all letters from combo are in word
        """
        for letter in set(combo):
            if not word.count(letter) >= combo.count(letter):
                return False
        return True

    def apply_guess(self, guess, num):
        """
        Applies the guess and stores the possible words left
        """
        self._calculate_and_store_combos(guess, num)
        self._possible_words = \
            self._narrow_wordpool(self._possible_words, guess, num)

    def _narrow_wordpool(self, possible_words, guess, num):
        """
        Cuts down the passed in possible_words, rather than
        the member variable
        """
        not_in, or_in = self._calculate_combos(guess, num)
        new_possible_words = []
        for word in possible_words:
            is_okay = True
            for combo in not_in:
                if self._combo_in_word(combo, word):
                    is_okay = False
                    break
            if not is_okay:
                continue

            is_okay = len(or_in) == 0
            for combo in or_in:
                if self._combo_in_word(combo, word):
                    is_okay = True
                    break

            if is_okay:
                new_possible_words.append(word)

        return new_possible_words

    def find_error(self, word):
        """
        Finds the answer that was given that disagrees with "word"
        :return: None if can't find any
        """
        for rule, guess in self._all_combos_not_in.items():
            for combo in rule:
                if self._combo_in_word(combo, word):
                    return guess
        for rule, guess in self._all_combos_or_in.items():
            for combo in rule:
                if self._combo_in_word(combo, word):
                    break
            else:
                return guess
        return None

    @staticmethod
    def _calculate_overlap(word1, word2):
        overlap = 0
        for letter in set(word1):
            overlap += min(word1.count(letter), word2.count(letter))
        return overlap

    def overlap_with_secret_word(self, word):
        return self._calculate_overlap(word, self._secret_word)

    def next_guess(self):
        if self._difficulty > 1:
            return self._get_best_next_guess()
        else:
            return random.choice(self._possible_words)

    def _get_best_next_guess(self, sample_size=100, verbose=True):
        min_score = len(self._possible_words) ** 2
        best_guesses = []
        sampling = random.sample(self._possible_words,
                                 min(sample_size, len(self._possible_words)))
        for i, guess in enumerate(sampling):

            words_left = [
                len(self._narrow_wordpool(sampling, guess, i))
                for i in range(6)
            ]

            n_overlaps = [0, 0, 0, 0, 0, 0]
            for possible_word in sampling:
                n_overlaps[
                    self._calculate_overlap(guess, possible_word)] += 1

                score = sum([overlap*n_words for (overlap, n_words) in
                             zip(n_overlaps, words_left)])
                if score > min_score:
                    break

            if score < min_score:
                best_guesses = [guess]
                min_score = score
            elif score == min_score:
                best_guesses.append(guess)
        return random.choice(best_guesses)


class BagelGame:

    CHEAT_WORD = 'cheat!'
    LIST_WORD = 'list!'
    SHOW_WORD = 'show!'

    def __init__(self, difficulty):
        self.ai = BagelAI(difficulty)
        self._guesses = {}
        self._n_turns = 0

    @staticmethod
    def _prompt(text):
        try:
            return raw_input(text)
        except:
            return input(text)

    def play(self):
        self._n_turns = 0
        self._guesses = {}
        self.ai.choose_new_word()
        print('Choose a word, and then...')
        win = False
        while True:
            win = self._human_turn()
            self._n_turns += 1
            if win:
                break
            lose = self._computer_turn()
            if lose:
                break
            if not self.ai.are_words_remaining():
                print('Your word is not in my dictionary, or you messed up...')
                your_word = ''
                while not len(your_word) == 5:
                    your_word = self._prompt('What was your word? ')
                if not self.ai.in_full_dict(your_word):
                    print('Sorry, but %s is not in my dictionary' % your_word)
                else:
                    mistake = self.ai.find_error(your_word)
                    print('You said that %s had %d correct letters!\n\n'%
                          (mistake[0], mistake[1]) +
                          'Why would you lie to me like that!!')
                break

        if not win:
            keep_playing = ''
            while not (keep_playing == 'yes' or keep_playing == 'no'):
                keep_playing = self._prompt('Would you like to keep guessing?')
            if keep_playing == 'yes':
                while not win:
                    win = self._human_turn()
            else:
                print('My word was %s'%self.ai.secret_word)

    def _human_turn(self):
        guessed_word = self._prompt('Guess a word: ').lower()
        while not self.ai.in_full_dict(guessed_word) \
                and not guessed_word == self.CHEAT_WORD:
            if guessed_word == self.LIST_WORD:
                pprint(self._guesses)
            if guessed_word == self.SHOW_WORD:
                pprint(self.ai._possible_words)

            guessed_word = self._prompt('Sorry... I don\'t know that word. Guess again: ')

        if self.ai.is_secret_word(guessed_word) \
                or guessed_word == self.CHEAT_WORD:
            print('You win!\nMy word was %s\nit took you %d guesses'%
                 (self.ai.secret_word, self._n_turns))
            return True

        overlap = self.ai.overlap_with_secret_word(guessed_word)

        self._guesses[guessed_word] = overlap

        print('%d letters from %s are in my word'%
              (overlap, guessed_word))
        return False

    def _computer_turn(self):
        guess = self.ai.next_guess()
        got_response = False
        num = 0
        while not got_response:
            response = self._prompt('How many letters from %s are in your word? '%
                             guess)
            try:
                num = int(response)
                got_response = True
            except:
                got_response = False

        if num == 5:
            answer = ''
            while (not answer.lower() == 'yes' ) and (not answer.lower() == 'no'):
                answer = self._prompt('Is %s your word?! '%guess)
            if answer.lower() == 'yes':
                print('I WINNN!')
                return True

        self.ai.apply_guess(guess, num)
        return False

class  BagelSolver:
    
    def __init__(self):
        self.ai = BagelAI(2)

    def prompt(self):
        word_and_num = ''
        while not re.match('[a-z]{5} [0-5]', word_and_num):
            word_and_num = BagelGame._prompt('Enter <word> <#>: ')

        return word_and_num[0:5], int(word_and_num[6])
                
    def solve(self):
        while True:
            word, num = self.prompt()
            self.ai.apply_guess(word, num)
            pprint(self.ai._possible_words)


if __name__ == '__main__':
    if 'solve' in sys.argv:
        BagelSolver().solve()
    else:
        BagelGame(2).play()
