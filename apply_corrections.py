#!/usr/bin/env python3

'''
Apply a list of corrections in the siaconf format to a corpus file
'''

import csv
import re
import sys
import os
from os.path import isfile, join


## Predefs

rule_pattern = re.compile("->\s(?P<input>\w*) [-=]> (?P<output>\w*)")
rules = {}


## Functions

def parseRule(line):
    '''
    Parses the list of rules given in the command line.
    Result is given as tuple (input, output), unless the line doesn't match
    rule_pattern.
    '''
    
    rule = rule_pattern.match(line)
    try:
        return (rule.group("input"), rule.group("output"))
    except AttributeError:
        print(line)
        return None


def correct(word):
    if word in rules.keys():
        return rules[word]
    else:
        return word

    
def applyRules(word_triple):
    try:
        token, pos, lemma = word_triple
        return (correct(token), pos, correct(lemma))
    except ValueError:
        return word_triple


#############
# Main land #
#############

# reading the corrections file
with open(sys.argv[1], 'r') as corrections:
    for line in corrections:
        rule = parseRule(line)
        if rule:
            rules[rule[0]] = rule[1]

print(str(len(rules.items())) + ' rules loaded.')
print('---------\n')

# reading corpus files from the path provided and applying rules
corpus_path = sys.argv[2]
corpus_files = [f for f in os.listdir(corpus_path) if isfile(join(corpus_path, f))]
try:
    os.mkdir(corpus_path + '_corr')
except OSError:
    pass

for text in corpus_files:
    in_path = join(corpus_path, text)
    out_path = join(corpus_path + '_corr', text)
    
    with open(in_path, 'r') as tsv:
        colonia_reader = csv.reader(tsv, delimiter='\t')

    # write corrected file on the new path
        with open(out_path, 'w') as tsv:
            corr_rows = map(applyRules, colonia_reader)
            colonia_writer = csv.writer(tsv, delimiter='\t')
            for row in corr_rows:
                if row:
                    colonia_writer.writerow(row)
