import pdb
import random
global good_words
dict_file = 'dictionary.txt'
global not_ins
not_ins = dict()

def setup_dict(dict_file):
    """
    loads all five letter words from a dictionary
    """
    global good_words
    all_words = [x.strip().lower() for x in open(dict_file).readlines()]
    good_words = []
    for word in all_words:
        if len(word)==5:
            good_words.append(word)

def your_turn(comp_word):
    """
    Calculates how many letters from your guess are in the comuter's word
    """
    global good_words
    my_word = raw_input("Guess a word: ").lower()
    while not my_word in good_words and not my_word=='cheat!':
        my_word = raw_input('That word isn\'t in my dictionary. Guess again: ')
    if my_word ==comp_word or my_word=='cheat!':
        print 'You win! My word was '+comp_word
        return True
    not_counted_letters = comp_word
    numLetters = 0
   # Kinda embarassed about how I'm doing this. There's gotta be a better way.
    for letter in my_word:
        if letter in not_counted_letters:
            not_counted_letters = not_counted_letters.replace(letter,'',1)
            numLetters+=1
    print str(numLetters)+' from '+my_word+' are in my word'
    return False

def letter_combos(word, length, start):
    """
    returns all of the possible combinations of 'length' letters
    that are present in the word 'word', starting at the position
    'start'. There is also probably a better way of going about
    doing this.
    """
    combos=[]
    letters = list(word)
    if length==1:
        return tuple([(x) for x in letters[start:]])
    for i in range(start, len(word)):
        this_letter = [word[i]]
        other_letters = letter_combos(word, length-1, i+1)
        for letter in other_letters:
            a = list(this_letter)
            a.extend(letter)
            combos.append(tuple(a))
    return tuple(combos)

def comp_turn(words_left):
    """
    Full computer's turn.
    """

    global not_ins #contains all of the combinations of letters that cannot be in the word

    # guesses a word randomly
    guess = words_left.pop(random.randint(0,len(words_left)-1))
    good = False
    while not good:
        num = raw_input('How many letters from '+guess+' are in your word? ')
        try:
            num = int(num)
            good = True
        except:
            good = False
    if num==5:
        answer = ''
        while (not answer.lower()=='yes') and (not answer.lower()=='no'):
            answer = raw_input('Is '+guess+' your word? ')
        if answer.lower()=='yes':
            print 'I win!!'
            return True

    # Gets all of the letter combinations that cannot be in the word.
    # eg. If the word is HOUSE, and you respond 2, not_in will contain
    # [(H,O,U),(H,O,S),(H,O,E),(H,U,S),(H,U,E),(H,S,E),(O,U,S)...]
    # as no word can contain all of the letters in any of those tuples
    not_in= letter_combos(guess, int(num)+1, 0)

    # Stores the current response so it can tell you later if you were wrong.
    not_ins[tuple(not_in)] = (guess, num)
    new_wordlist = []

    # Cycle through all of the words left in the dictionary
    for word in words_left:
        is_okay = True
        # Look through all of the bad combinations
        for combo in not_in:
            all_letters = True
            word_check = word
            # Again, there's got to be a better way to do this.
            # It makes a copy of the word, then goes through that word
            # letter by letter, removing letters if they're in 
            # the bad combination in question. If it finds that not
            # all of the letters in the bad combo are in the word, then
            # it's fine. 
            for letter in combo:
                if letter not in word_check:
                    all_letters = False
                    break
                word_check = word_check.replace(letter,'',1)
            if all_letters:
                is_okay = False
                break
        if is_okay:
            new_wordlist.append(word)
    # or_in contains tuples of letter combinations that /must/ be in the
    # word. If the word is HOUSE, and you respond 2, or_in will contain
    # [(H,O), (H,U), (H,S), (H,E), (O,U), (O,S), (O,E) ...]
    # as any viable word must contain all of the letters in at least
    # one of those words.
    or_in = letter_combos(guess, int(num), 0)
    new_wordlist_2 = []
    for word in new_wordlist:
        if not len(or_in)==0:
            is_okay = False 
        else:
            is_okay = True
        for combo in or_in:
            word_check = word
            all_letters = True
            for letter in combo:
                if letter not in word_check:
                    all_letters = False
                    break
                word_check = word_check.replace(letter,'',1)
            if all_letters:
                is_okay = True
                break
        if is_okay:
            new_wordlist_2.append(word)
    print new_wordlist_2
    return new_wordlist_2

def find_error(word):
    """
    Looks through your responses to find if you made an error
    """
    global not_ins
    for rule in not_ins.keys():
        for combo in rule:
            all_letters = True
            word_check = word
            for letter in combo:
                if letter not in word_check:
                    all_letters = False
                    break
                word_check = word_check.replace(letter,'',1)
            if all_letters:
                return not_ins[rule]
def play():
    global good_words
    setup_dict(dict_file)
    words_left = good_words
    comp_word = good_words[random.randint(0, len(good_words)-1)]
    show_dict = raw_input('Type Y to show dictionary')
    if show_dict=='Y':
        print good_words
    print 'Choose a word, and then ...'
    win = your_turn(comp_word)
    lose = False
    while not win and not lose:
        words_left = comp_turn(words_left)
        if not words_left==True and len(words_left)==0:
            print 'Your word is not in my dictionary, or you messed up.'
            your_word = ''
            while not len(your_word)==5:
                your_word = raw_input('What was your word? ')
            if not your_word in good_words:
                print 'Sorry, '+your_word+' is not in my dictionary'
            else:
                mistake = find_error(your_word)
                print 'You said that '+mistake[0]+' had '+str(mistake[1])+' correct letters. You lied.'
            lose = True
        if not lose:
            win = your_turn(comp_word)
        if words_left == True:
            lose = True
    keep_playing = ''
    while not (keep_playing=='yes' or keep_playing=='no'):
        keep_playing = raw_input('Would you like to keep guessing my word?')
    if keep_playing.lower()=='yes':
        while not win:
            win = your_turn(comp_word)
    else:
        print 'my word was ' + comp_word

if __name__ == "__main__":
    play()
