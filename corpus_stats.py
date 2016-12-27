#!/usr/bin/env python3

'''
Get frequencies by year for the full corpus and write them to the disk for ref.
'''

import nltk
import pandas as pd
import numpy as np
import datation
import gendatasets

# Loading the full wordlist and cleaning it up
print('Reading file...')
full_df = pd.read_table(gendatasets.FULL_WL)

print('Splitting metadata')
full_df = gendatasets.split_filename(full_df)

print('Cleaning up and resolving unknown lemmas')
full_df = full_df[full_df['token'].str.contains(r'\w+(-\w+)?')]
full_df['lemma'] = full_df.where(full_df == '<unknown>',
                                 full_df.token, axis='index')

print('Normalizing datations')
full_df = datation.date_wl(full_df)

print('Generating frequency list and stats')
stats = {}
for year in set(full_df.year.values):
    words = full_df.lemma[full_df.year == year]
    fd = nltk.FreqDist(words)
    stats[year] = np.array((fd.N(), fd.B(), len(fd.hapaxes())))

print(stats)
full_corpus_stats_df = pd.DataFrame.from_dict(stats, orient='index')
full_corpus_stats_df.columns = ['token', 'type', 'hapaxes']

print('Writing datasets to disk')
full_df.to_csv('datasets/full_df.tsv', sep='\t')
full_corpus_stats_df.to_csv('datasets/full_corpus_stats_df.tsv', sep='\t')
