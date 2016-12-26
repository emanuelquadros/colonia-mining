#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import os
from statistics import mean
from math import ceil
import nltk
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import datation
plt.style.use('ggplot')

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

    bottom = int(center_y - round(w/2))
    top = int(center_y + ceil(w/2) + 1)
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
        l = []
        for y in range(p[0], p[1]):
            if y in dic.keys():
                l.extend(dic[y].tolist())
        midpoint = int(ceil(mean(p)))
        #if midpoint==1795: import pdb; pdb.set_trace()
        data[midpoint] = l

    #for d in data.keys():
    #    print(str(d) + ' ' + str(len(data[d])))

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

    out_dic = {}
    for (key, value) in dic.items():
        out_dic[key] = nltk.FreqDist(value)
    return out_dic


def apply_exclusions(df, excl, cols=['token','lemma']):
    for col in cols:
        df = df[df[col].isin(excl) == False]
    return df


def basicstats(fd, corpus_counts):
    '''
    Given a frequency distribution and corpus counts,
    compute basic stats for Baayen's metrics.
    '''

    n_1 = len(fd.hapaxes())
    corpus_hapaxes = corpus_counts[2]
    #corpus_types = corpus_counts[1]
    corpus_tokens = corpus_counts[0]

    return (
        fd.N(),
        fd.B(), # types, realized productivity
        n_1, # hapax legomena
        n_1 / corpus_hapaxes, # expanding productivity
        n_1 / fd.N(), # potential productivity
        (fd.B() / corpus_tokens) * 1000000, # typer per million words
        int(corpus_tokens)
    ) 


def df_from_freqs(dic, w=33):
    '''
    Input: dict of FreqDists
    Output: pandas df with basic stats per row
    '''

    rows = {}
    for year in dic.keys():
        year_counts = corpus_stats(year, w)
        try:
            rows[year] = np.array(basicstats(dic[year], year_counts))
        except ZeroDivisionError:
            print(year)
            print(dic[year])
            print(year_counts)
            import sys; sys.exit(1)

    out_df = pd.DataFrame.from_dict(rows, orient='index')
    out_df.columns = ['tokens', 'types', 'hapaxes',
                      'expandingP', 'potentialP', 'types_normed', 'corpus_N']

    return out_df


def stats_from_dict(dic, corpus_df):
    '''
    Expects a dictionary of frequency distributions and computes Baayen's
    metrics for each of them. Returns a dict.
    '''

    for (key, value) in dic.items():
        corpus_df = corpus_df[corpus_df.year == key]
        dic[key] = basicstats(value, corpus_df)
    return dic


def plotting(dataframe):
    """
    Just plots whatever configuration of the data I want.
    """
    
    plt.figure()
    fig, axes = plt.subplots(nrows=2, ncols=2)
    dataframe['expandingP'].plot(ax=axes[0,0], logy=True);
    axes[0,0].set_title('Expanding productivity')
    dataframe['types_normed'].plot(ax=axes[1,1], logy=True);
    axes[1,1].set_title('Type count, normalized')
    dataframe['types'].plot(ax=axes[1,0], logy=True);
    axes[1,0].set_title('Type count')
    dataframe['potentialP'].plot(ax=axes[0,1], logy=True);
    axes[0,1].set_title('Potential productivity')
    plt.figure()
    fig, axes = plt.subplots(nrows=2, ncols=2)
    dataframe['expandingP'].plot(ax=axes[0,0]);
    axes[0,0].set_title('Expanding productivity')
    dataframe['types_normed'].plot(ax=axes[1,1]);
    axes[1,1].set_title('Type count, normalized')
    dataframe['types'].plot(ax=axes[1,0]);
    axes[1,0].set_title('Type count')
    dataframe['potentialP'].plot(ax=axes[0,1]);
    axes[0,1].set_title('Potential productivity')
    plt.figure()
    dataframe['corpus_N'].plot()
    # dataframe.plot(y=['types_normed'], title='Type count, normalized')
    # dataframe.plot(y=['types'], title='Type count')
    # dataframe.plot(y=['potentialP'], title='Potential productivity')

    dataframe_filtered = dataframe.apply(savgol_filter, args=(49, 2))
    plt.figure()
    fig, axes = plt.subplots(nrows=2, ncols=2)
    dataframe_filtered['expandingP'].plot(ax=axes[0,0]);
    axes[0,0].set_title('Expanding productivity-filtered')
    dataframe_filtered['types_normed'].plot(ax=axes[1,1]);
    axes[1,1].set_title('Type count, normalized-filtered')
    dataframe_filtered['types'].plot(ax=axes[1,0]);
    axes[1,0].set_title('Type count-filtered')
    dataframe_filtered['potentialP'].plot(ax=axes[0,1]);
    axes[0,1].set_title('Potential productivity-filtered')
    
    plt.show()


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

    # Cleaning up
    merged_df = merged_df.where(merged_df != '<unknown>',
                                merged_df.token, axis=0)
    merged_df.year = pd.to_numeric(merged_df.year)

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
    tby_mento = {}
    tby_cao = {} # token by year
    for year in years:
        current_tokens = merged_df[merged_df.year == year]
        current_tokens_mento = current_tokens.lemma[current_tokens.suffix == 'mento']
        current_tokens_cao = current_tokens.lemma[current_tokens.suffix == 'cao']
        tby_mento[year] = current_tokens_mento
        tby_cao[year] = current_tokens_cao
        # pos = pd.Timestamp(str(year+delta) + '-12-31').strftime('%Y-%m-%d')
    tbepoch_mento = df_from_freqs(freqdist_from_dict(roll(tby_mento, 33)))
    tbepoch_cao = df_from_freqs(freqdist_from_dict(roll(tby_cao, 33)))

    # plotting
    tbmerged = pd.concat([tbepoch_cao, tbepoch_mento],
                         keys=['cao', 'mento'],
                         names=['cao', 'mento']).unstack(0)

    # Selecting only the epochs that are likely to be the most representative.
    # Guess taken from Tang & Nevin 2013.
    tbmerged_621 = tbmerged[tbmerged.corpus_N >= 621190].dropna()

    # Guess
    tbmerged_100 = tbmerged[tbmerged.corpus_N >= 100000].dropna()
    
    tbmerged.to_csv('datasets/tbmerged.tsv', '\t')
    

    # Output datasets and debugging files
    # try:
    #     os.mkdir('datasets')
    # except FileExistsError:
    #     pass
    # finally:
    #     os.chdir('datasets')
    #     cao_df.to_csv('cao.csv', sep='\t')
    #     mento_df.to_csv('mento.csv', sep='\t')
    #     #mento_freq.to_csv('mento_freqdist.csv', sep='\t')
    #     #cao_freq.to_csv('cao_freqdist.csv', sep='\t')
    #     merged_df.to_csv('merged.csv', sep='\t')

    #     tbepoch_cao.to_csv('tokens_by_epoch_cao.tsv', sep='\t')
    #     tbepoch_mento.to_csv('tokens_by_epoch_mento.tsv', sep='\t')

    #     # Save freq dist for each year
    #     #for year, fdist in freq_dists.items():
    #     #    fdist.to_csv(str(year) + '.tsv', sep='\t')

    # # Debugging - sanity checks, etc.
    # os.chdir('../')
    # try:
    #     os.mkdir('debug')
    # except FileExistsError:
    #     pass
    # finally:
    #     os.chdir('debug')

    #     # Write a list of words not tagged as nouns
    #     non_nouns_df = merged_df[merged_df['pos'] != 'NOM']
    #     non_nouns_df.to_csv('notNOMs.tab', sep='\t')

    #     # Write a list of tokens with non-nominalized lemmas
    #     wrong_lemmas_df = merged_df[merged_df['lemma'].str[-1:] != 'o']
    #     wrong_lemmas_df.to_csv('wrong_lemmas.tab', sep='\t')
