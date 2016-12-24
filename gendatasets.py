#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import re
import os
from statistics import mean
from math import ceil
import nltk
import datation
import pandas as pd
import numpy as np

CAO_WL = 'colonia_cao.lst'
MENTO_WL = 'colonia_mento.lst'
FULL_WL = 'full_wordlist.lst'
EXCLUSIONS_FILE = 'exclusions.lst'
CORPUS_STATS = pd.read_table('datasets/full_corpus_stats_df.tsv',
                             sep='\t', index_col=0)


def corpus_stats(center_y, w):
    '''
    Input: year at the center of the window, window size
    Output: a tuple (tokens, types, hapaxes)
    '''

    bottom = center_y - round(w/2)
    top = center_y + ceil(w/2) + 1
    window = range(bottom, top)

    cstats_subset = CORPUS_STATS[CORPUS_STATS.index.isin(window)]
    cstats_subset_sums = cstats_subset.sum(axis=0)
    
    return (cstats_subset_sums['token'],
            cstats_subset_sums['type'],
            cstats_subset_sums['hapaxes'])


def roll(dic, w):
    '''
    Given a dictionary with numbers as keys, interpreted as time labels, returns
    a dictionary with values resampled in a rolling window of size w.

    Dictionary values are expected to be lists.
    '''
    bottom = min(dic.keys())
    top = max(dic.keys())
    epochs = [(i, i+w) for i in range(bottom, top - w + 2)]

    data = {}

    for p in epochs:
        for year in range(p[0], p[1]):
            if year in dic.keys():                
                l.extend(dic[year])
        data[round(mean(p))] = l
        
    return data


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


def freqdist_from_dict(dic):
    '''
    Expects a dictionary of lists of strings. Returns a dictionary of frequency
    distributions.
    '''
    for (key, value) in dic.items():
        dic[key] = nltk.FreqDist(value)
    return dic


def apply_exclusions(df, excl, cols=['token','lemma']):
    for col in cols:
        df = df[df[col].isin(excl) == False]
    return df


def basicstats(fd, corpus_df):
    '''
    Given a frequency distribution, compute basic stats for Baayen's metrics.
    '''

    n_1 = len(fd.hapaxes())

    return (fd.N(),
            fd.B(), # types, realized productivity
            n_1,
            n_1 / corpus_fd.hapaxes(), # expanding productivity
            n_1 / fd.N()# potential productivity
    )


def stats_from_dict(dic, corpus_df):
    '''
    Expects a dictionary of frequency distributions and computes Baayen's
    metrics for each of them. Returns a dict.
    '''

    for (key, value) in dic.items():
        corpus_df = corpus_df[corpus_df.year == key]
        dic[key] = basicstats(value, corpus_df)
    return dic

            
if __name__ == "__main__":
    

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
    years = [int(y) for y in dby.groups.keys()]

    # Time series
    delta = 178
    time_index = pd.date_range(str(min(years) + delta),
                               str(max(years) + delta), freq='A')
    tokens_by_year = pd.DataFrame(index=time_index,
                                  columns=['tokens'])
    stats_by_year = pd.DataFrame(index=time_index,
                                 columns=['tokens', 'types', 'hapax'])

    # token time series
    tby_mento, tby_cao = {} # token by year
    for year in years:
        current_tokens = merged_df[merged_df.year == str(year)]
        current_tokens_mento = current_tokens.lemma[current_tokens.suffix == 'mento']
        current_tokens_cao = current_tokens.lemma[current_tokens.suffix == 'cao']
        tby_mento[year] = current_tokens_mento
        tby_cao[year] = current_tokens_cao
        # pos = pd.Timestamp(str(year+delta) + '-12-31').strftime('%Y-%m-%d')
    tbepoch_mento = freqdist_from_dict(roll(tby_mento))
    tbepoch_cao = freqdist_from_dict(roll(tby_cao))

    #mento_stats = 

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

        tokens_by_year[tokens_by_year['tokens'].notnull()].to_csv(
            'tokens_by_year.csv', sep='\t')

        # Save freq dist for each year
        #for year, fdist in freq_dists.items():
        #    fdist.to_csv(str(year) + '.tsv', sep='\t')

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
