#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import csv
import nltk
import re
import pandas as pd
import os


cao_wl = 'colonia_cao.lst'
mento_wl = 'colonia_mento.lst'
exclusions_file = 'exclusions.lst'


def splitFilename(df):
    '''
    Creates text and year column, which are important pieces of metadata.
    '''
    
    df['text'] = df.token.str.extract('\./(.*.txt)')
    df['token'] = df.token.str.extract(':(.*)')
    df['token'] = df.token.str.lower()

    year_regex = '(\d\d\d\d|\d\dth)'
    df['year'] = df.text.str.extract(year_regex)

    return df


def freqDist(series):
    freqs = nltk.FreqDist(series).most_common()
    return pd.DataFrame(freqs, columns=['word', 'freq'])


def applyExclusions(df, excl, cols = ['token', 'lemma']):
    for col in cols:
        df = df[df[col].isin(excl) == False]
    return df

# Load exclusions file:
with open(exclusions_file, 'r') as exc:
    exclusions = [line.strip() for line in exc]

# Read data frames
cao_df = pd.read_table(cao_wl)
cao_df = splitFilename(cao_df)
cao_df = applyExclusions(cao_df, exclusions)
mento_df = pd.read_table(mento_wl)
mento_df = splitFilename(mento_df)
mento_df = applyExclusions(mento_df, exclusions)

merged_df = pd.concat([cao_df, mento_df], ignore_index = True,
                      keys = ['cao', 'mento'])

# Generate frequency distributions from the datasets
mento_freq = freqDist(mento_df.token)
cao_freq = freqDist(cao_df.token)

# Output datasets and debugging files
try:
    os.mkdir('datasets')
except FileExistsError:
    pass
finally:
    os.chdir('datasets')
    cao_df.to_csv('cao.csv', sep='\t')
    mento_df.to_csv('mento.csv', sep='\t')
    mento_freq.to_csv('mento_freqdist.csv', sep='\t')
    cao_freq.to_csv('cao_freqdist.csv', sep='\t')
    merged_df.to_csv('merged.csv', sep='\t')

# Debugging - sanity checks, etc.
os.chdir('../')
try:
    os.mkdir('debug')
except FileExistsError:
    pass
finally:
    os.chdir('debug')

    # Write a list of words not tagged as nouns
    non_nouns_df = merged_df[merged_df['pos'] != 'NOM']
    non_nouns_df.to_csv('notNOMs.tab', sep='\t')

    # Write a list of tokens with non-nominalized lemmas
    wrong_lemmas_df = merged_df[merged_df['lemma'].str[-1:] != 'o']
    wrong_lemmas_df.to_csv('wrong_lemmas.tab', sep='\t')
