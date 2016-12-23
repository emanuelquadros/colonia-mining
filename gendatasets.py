#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import csv
import nltk
import re
import pandas as pd
import os
import datation

CAO_WL = 'colonia_cao.lst'
MENTO_WL = 'colonia_mento.lst'
FULL_WL = 'full_wordlist.lst'
EXCLUSIONS_FILE = 'exclusions.lst'


def split_filename(df):
    '''
    Creates text and year column, which are important pieces of metadata.
    '''

    df['text'] = df.token.str.extract(r'\./(.*.txt)')
    df['token'] = df.token.str.extract(r':(.*)')
    df['token'] = df.token.str.lower()

    year_regex = r'(\d\d\d\d|\d\dth)'
    df['year'] = df.text.str.extract(year_regex)

    return df


def freqdist(series):
    freqs = nltk.FreqDist(series).most_common()
    return pd.DataFrame(freqs, columns=['word', 'freq'])


def apply_exclusions(df, excl, cols=['token', 'lemma']):
    for col in cols:
        df = df[df[col].isin(excl) == False]
    return df

# Load exclusions file
with open(EXCLUSIONS_FILE, 'r') as exc:
    exclusions = [line.strip() for line in exc]

# Read data frames
cao_df = pd.read_table(CAO_WL)
cao_df = split_filename(cao_df)
cao_df = apply_exclusions(cao_df, exclusions)
cao_df['suffix'] = 'cao'
cao_df = datation.date_wl(cao_df)
mento_df = pd.read_table(MENTO_WL)
mento_df = split_filename(mento_df)
mento_df = apply_exclusions(mento_df, exclusions)
mento_df['suffix'] = 'mento'
mento_df = datation.date_wl(mento_df)

# Loading the full wordlist and cleaning it up
#full_df = pd.read_table(FULL_WL)
#full_df = split_filename(full_df)
#full_df = full_df[full_df['token'].str.match('\w+-?\w+')]
#full_df['lemma'] = full_df.where(full_df == '<unknown>',
#                                 full_df.token, axis='index')
#full_df.to_csv('debug/teste2.csv', sep='\t')

# merging the suffixes data frames
merged_df = pd.concat([cao_df, mento_df], ignore_index=True,
                      keys=['cao', 'mento'], names=['cao', 'mento'])
merged_df = merged_df.where(merged_df != '<unknown>',
                            merged_df.token, axis=0)

# Generate frequency distributions from the datasets
mento_freq = freqdist(mento_df.token)
cao_freq = freqdist(cao_df.token)

# Compute general corpus stats
#full_freq = freqdist(full_df.lemma)

# Data grouped by year
dby = merged_df.groupby('year')
years = [y for y in dby.groups.keys()]
freq_dists = {}
for year in year:
    freq_dists[year] = freqdist(dby.get_group(year))

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

    # Save freq dist for each year
    for year, fdist in freq_dists:
        fdist.to_csv(year + '.tsv', sep='\t')

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
