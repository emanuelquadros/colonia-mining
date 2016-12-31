#!/usr/bin/env python3


import bayesian_changepoint_detection.offline_changepoint_detection as offcd
from functools import partial
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
plt.style.use('ggplot')


def plot_changepoint(data, col, interval=10, title='', output=''):
    """
    data: data frame
    col: column in the data frame
    interval: interval of years to show in the x-axis
    ci = if True, plot confidence intervals
    """

    print('Computing change point for', title)

    # Changepoint detection
    Q, P, Pcp = offcd.offline_changepoint_detection(
        data[col],
        partial(offcd.const_prior,
                l=(len(data[col])+1)),
        offcd.gaussian_obs_log_likelihood,
        truncate=-40
    )

    print('Plotting...')

    # Getting info for the x-axis
    indexes = data.index[data.index % interval == 0].tolist()
    labels = list(map(str, indexes))
    time_ticks = np.where(data.index.isin(indexes))[0].tolist()

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1)

    line = savgol_filter(data[col], 33, 3)

    ax1.plot(range(len(data.index)), line)
    ax1.plot(range(len(data.index)), data[col], '.', ms=2)
    ax1.set_xticks(time_ticks)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel(title)

    ax2.plot(np.exp(Pcp).sum(0))
    ax2.set_ylim([0,1])
    ax2.set_xticks(time_ticks)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel('Probability')
    
    if output:
        filename = output
    else:
        min_sample_size = min(data.corpus_N)
        filename=title.lower() + str(min_sample_size) + '.png'
    plt.savefig(filename)


if __name__ == "__main__":

    cao = pd.read_table('datasets/cao_resampled.tsv', index_col=0)
    mento = pd.read_table('datasets/mento_resampled.tsv', index_col=0)

    plot_changepoint(cao, 'types', 50, 'Realized productivity (ção)',
                     'types_cao.png')
    plot_changepoint(mento, 'types', 50, 'Realized productivity (mento)',
                     'types_mento.png')
    plot_changepoint(cao, 'hapaxes', 50, 'Potential productivity (ção)',
                     'hapaxes_cao.png')
    plot_changepoint(mento, 'hapaxes', 50, 'Potential productivity (mento)',
                     'hapaxes_mento.png')
