#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Basic statistics of data chunk.
"""

__credits__ = "ICOS Carbon Portal"
__license__ = "GPL-3.0"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']
__status__ = "rc1"
__date__ = "2023-03-23"

import pandas as pd


def corr_table(df: pd.DataFrame) -> pd.DataFrame:
    return df.corr()


def data_span(df: pd.DataFrame) -> dict:
    d = dict()
    rows = len(df)
    d['timeslots'] = rows
    d['sample_start'] = df['TIMESTAMP'][0].strftime('%Y-%m-%d %X')
    d['sample_end'] = df['TIMESTAMP'][rows-1].strftime('%Y-%m-%d %X')
    return d


def basic_statistics(df: pd.DataFrame) -> pd.DataFrame:
    rows = len(df)
    d = df.describe().T
    d['nan_values'] = rows - d['count']
    d['std'] = df.std()
    d = d[['count', 'nan_values', 'mean',
           'min', 'max',
           '25%', '50%', '75%', 'std']]
    d.rename(columns={'50%': '50% (median)'}, inplace=True)
    return d.T

