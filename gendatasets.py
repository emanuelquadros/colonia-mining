#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import os
from statistics import mean
from math import ceil
import nltk
import random
import pandas as pd
import numpy as np
import scipy.stats as st
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

    bottom = int(center_y - ceil(w/2))
    top = int(center_y + round(w/2))
    window = map(str, range(bottom, top))

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
        data[midpoint] = l

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
    corpus_tokens = corpus_counts[0]

    return (
        fd.N(),
        fd.B(), # types, realized productivity
        n_1, # hapax legomena
        n_1 / corpus_hapaxes, # expanding productivity
        n_1 / fd.N(), # potential productivity
        (fd.B() / corpus_tokens) * 1000000, # types per million words
        int(corpus_tokens)
    ) 


def random_sample(fdist, sample_size, runs=1000):
    """
    Given an nltk.FreqDist, compute frequency distributions from random
    of the data.

    Returns the means for type count and number of hapaxes, with
    confidence intervals: ((mean (min, max)), (mean (min, max)))
    """

    stats_pool = []
    
    for x in range(0, runs):
        sample = nltk.FreqDist(random.sample(list(fdist.elements()),
                                             sample_size))
        stats_pool.append(
            (
                sample.B(), #number of types, realized productivity
                len(sample.hapaxes()), # number of hapax legomena
            )
        )

    stats_pool = np.array(stats_pool)
    mean_types = st.bayes_mvs(stats_pool[:, 0])
    mean_hapaxes = st.bayes_mvs(stats_pool[:, 1])

    return mean_types, mean_hapaxes


def df_from_resampling(dic, sample_size=131):
    """
    Input: dict of FreqDist

    Output: data frame with means and CIs from random_sample
    """

    rows={}
    for year, fdist in sorted(dic.items()):
        if fdist.N() >= sample_size:
            print('Resampling', year)
            mean_types, mean_hapaxes = random_sample(fdist, sample_size)
            tmean, (t1, t2) = mean_types[0]
            hmean, (h1, h2) = mean_hapaxes[0]
            rows[year] = np.array((tmean, t1, t2,
                                   hmean, h1, h2,
                                   sample_size))

    out_df = pd.DataFrame.from_dict(rows, orient='index')
    out_df.columns = ['types', 'min_types', 'max_types',
                      'hapaxes', 'min_hapaxes', 'max_hapaxes',
                      'corpus_N']

    return out_df


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


def plot_data(dataframe):
    """
    Just plots whatever configuration of the data I want.
    """
    
    fig, axes = plt.subplots(2)
    dataframe['expandingP'].plot(ax=axes[0], logy=True);
    axes[0].set_title('Expanding productivity')
    dataframe['types_normed'].plot(ax=axes[1], logy=True);
    axes[1].set_title('Type count, normalized')
    for ax in np.ndenumerate(axes):
        ax[1].legend(['ção', 'mento'])

    fig, axes = plt.subplots(2)
    dataframe['expandingP'].plot(ax=axes[0]);
    axes[0].set_title('Expanding productivity')
    dataframe['types_normed'].plot(ax=axes[1]);
    axes[1].set_title('Type count, normalized')
    for ax in np.ndenumerate(axes):
        ax[1].legend(['ção', 'mento'])

    plt.figure()
    dataframe['corpus_N'].plot(legend=None)
    plt.title('Size of the corpus at each period (Corpus Colonia)')
    plt.xlabel('Period')
    
    dataframe_filtered = dataframe.apply(savgol_filter, args=(33, 2))
    fig, axes = plt.subplots(2)
    dataframe_filtered['expandingP'].plot(ax=axes[0]);
    axes[0].set_title('Expanding productivity (filtered)')
    dataframe_filtered['types_normed'].plot(ax=axes[1]);
    axes[1].set_title('Type count, normalized (filtered)')
    for ax in np.ndenumerate(axes):
        ax[1].legend(['ção', 'mento'])
    
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

    # token time series - rolling window
    tby_mento = {}
    tby_cao = {} # token by year
    for year in years:
        current_tokens = merged_df[merged_df.year == year]
        current_tokens_mento = current_tokens.lemma[current_tokens.suffix == 'mento']
        current_tokens_cao = current_tokens.lemma[current_tokens.suffix == 'cao']
        tby_mento[year] = current_tokens_mento
        tby_cao[year] = current_tokens_cao

    # They see me rolling...
    mento_fdists = freqdist_from_dict(roll(tby_mento, 33))
    cao_fdists = freqdist_from_dict(roll(tby_cao, 33))

    # Building the dataframes (without random sampling)
    tbepoch_mento = df_from_freqs(mento_fdists)
    tbepoch_cao = df_from_freqs(cao_fdists)

    mento_resampled = df_from_resampling(mento_fdists)
    cao_resampled = df_from_resampling(cao_fdists)
    mento_resampled.to_csv('datasets/mento_resampled.tsv', '\t')
    cao_resampled.to_csv('datasets/cao_resampled.tsv', '\t')

    # merging everything
    tbmerged = pd.concat([tbepoch_cao, tbepoch_mento],
                         keys=['cao', 'mento'])
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
