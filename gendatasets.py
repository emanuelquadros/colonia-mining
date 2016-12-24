#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import re
import os
from statistics import mean
import nltk
import datation
import pandas as pd
import numpy as np

CAO_WL = 'colonia_cao.lst'
MENTO_WL = 'colonia_mento.lst'
FULL_WL = 'full_wordlist.lst'
EXCLUSIONS_FILE = 'exclusions.lst'


def roll(dic, w):
    ## 33 is the magic window
    bottom = min(dic.keys())
    top = max(dic.keys())
    epochs = [(i, i+w) for i in range(bottom, top - w + 2)]

    data = {}

    for p in epochs:
        l = []
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


def freqdist(series):
    return nltk.FreqDist(series)
    #return pd.DataFrame(freqs, columns=['word', 'freq'])


def apply_exclusions(df, excl, cols=['token','lemma']):
    for col in cols:
        df = df[df[col].isin(excl) == False]
    return df


def basicstats(fd):
    '''
    Given a frequency distribution, compute basic stats for Baayen's metrics.
    '''

    return (fd.N(),
            fd.B(), # types, realized productivity
            fd.hapaxes())
            
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
    years = [int(y) for y in dby.groups.keys()]

    # Time series
    delta = 178
    time_index = pd.date_range(str(min(years) + delta),
                               str(max(years) + delta), freq='A')
    tokens_by_year = pd.DataFrame(index=time_index,
                                  columns=['tokens'])
    stats_by_year = pd.DataFrame(index=time_index,
                                 columns=['tokens', 'types', 'hapax'])

    # stats
    #for year in years:
    #    pos = pd.Timestamp(str(year+delta) + '-12-31').strftime('%Y-%m-%d')
    #    ydata = dby.get_group(year)
    #    fmento = freqdist(ydata[ydata['suffix'] == 'mento'])
    #    fcao = freqdist(ydata[ydata['suffix'] == 'cao'])
    #    mento_stats = basicstats(fmento)
    #    if pos in stats_by_year.index:
    #        stats_by_year.tokens[pos] = ','.join(current_tokens)
    #    else:
    #        print(pos)
    #        print('sir, we have a problem')


    # token time series
    tby = {} # token by year
    for year in years:
        current_tokens = merged_df.lemma[merged_df.year == str(year)]
        tby[year] = current_tokens        
        # pos = pd.Timestamp(str(year+delta) + '-12-31').strftime('%Y-%m-%d')
    tbepoch = roll(tby)

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
