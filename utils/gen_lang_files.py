#!/usr/bin/env python
import sys
from os import path

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: %s dataset_dir' % sys.argv[0]
        sys.exit(1)

    dataset_dir = sys.argv[1]
    words_pth   = path.join(dataset_dir, 'allwords.txt')
    sep_words_pth   = path.join(dataset_dir, 'sep_words.txt')
    chars_pth   = path.join(dataset_dir, 'chars.txt')
    lexicon_pth = path.join(dataset_dir, 'lexicon.txt')

    print 'Loading words:', words_pth
    with open(words_pth) as f:
        allwords = f.readlines()

    # sorted unique words
    allwords = sorted(set([l.strip() for l in allwords]))

    # save lines
    lines = [' '.join(l)+'\n' for l in allwords]
    print 'Saving lines to:', sep_words_pth
    with open(sep_words_pth, 'w') as f:
        f.writelines(lines)

    # sorted unique chars
    chars = sorted(set(''.join(allwords)))

    # save lexicon
    lexicon = [c+' '+c+'\n' for c in chars]
    lexicon.insert(0, '<SIL> sil\n')
    print 'Saving lexicon:', lexicon_pth
    with open(lexicon_pth, 'w') as f:
        f.writelines(lexicon)

    # save chars
    print 'Saving chars:', chars_pth
    with open(chars_pth, 'w') as f:
        f.writelines([c+'\n' for c in chars])