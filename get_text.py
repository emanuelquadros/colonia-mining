#!/usr/bin/env python3

'''
Gets the sentences from Colonia.
'''

import csv
import nltk
import re
import string
from os import listdir
from os.path import isfile, join

corpus_path = './Colonia_Corpus/'
output_path = './Colonia_Corpus_text/'
corpus_files = [f for f in listdir(corpus_path) if isfile(join(corpus_path, f))]

for text in corpus_files:
    # read
    print(text)
    with open(join(corpus_path, text), 'r') as tsv:
        rows = list(csv.reader(tsv, delimiter='\t'))
        rows = [r for r in rows if r]
        tokens = map(lambda r: r[0], rows)
        tokens = map(lambda token: re.sub('.*QUOTE', '\"', token), tokens)
        tokens = [t for t in filter(lambda token: token[0] != '<', tokens)]
        output = ' '.join(tokens).split('.')

    #write
    with open(output_path + text[:-4] + 'running.txt', 'w') as out:
        for sent in output:
            out.write(sent + '\n')
