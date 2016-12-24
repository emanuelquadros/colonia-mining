#!/usr/bin/env python3

'''
Create the datasets I need.
'''

import pandas as pd

cao_wl = 'colonia_cao.lst'
mento_wl = 'colonia_mento.lst'
cao_df = pd.read_table(cao_wl)
mento_df = pd.read_table(mento_wl)

datations = [('vieira17th.txt', 1670),
             ('camoes16th.txt', 1580),
             ('faria16th.txt', 1624), # correct
             ('guerreiro16th.txt', 1590), # pretty sure
             ('vicente16th.txt', 1522),
             ('almeida17th.txt', 1630),
             ('brochado17th.txt', 1690),
             ('matos17th1.txt', 1679), # didn't publish during his lifetime
             ('matos17th2.txt', 1679), # didn't publish during his lifetime
             ('garcao18th.txt', 1778)]

def date_wl(df):
    for (txt, year) in datations:
        df.ix[df.text==txt, 'year'] = year
    return df
