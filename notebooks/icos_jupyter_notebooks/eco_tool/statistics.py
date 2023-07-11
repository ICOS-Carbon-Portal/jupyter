#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Purpose of code
"""

__credits__ = "ICOS Carbon Portal"
__license__ = "GPL-3.0"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']
__status__ = "rc1"
__date__ = "2023-03-23"

import pandas as pd


# import numpy as np
# import seaborn as sns
# from fitter import Fitter, get_common_distributions, get_distributions

def statistics(df: pd.DataFrame) -> dict:
    """
    Calculates statistics of the columns of df.
    The columns of distr_df are expected to be
    distributions of the columns of df.

    Parameters:
        df: pd.DataFrame

    :return:
        dict
    """

    def nan_values(f):
        return len(f) - len(f.dropna())

    def E(f):
        """
        E for expectation
        """
        if isinstance(f, pd.DataFrame):
            return f.sum() / len(f)

    def mean(f):
        return E(f)

    def st_dev(f, mu):
        return E((f - mu) ** 2) ** (1 / 2)

    def bessel_st_dev(f):
        """
        pandas standard method,
        see `https://en.wikipedia.org/wiki/Bessel%27s_correction`
        """
        return f.std()

    def covariance(X: object, Y: object, mean_X: object, mean_Y: object) -> object:
        return mean((X - mean_X) * (Y - mean_Y))

    if isinstance(df, pd.DataFrame):
        c_ls = list(df.columns)
        # we cannot use a IcosFrame here
        df = pd.DataFrame(df)
    else:
        return {}

    d = {'timeslots': len(df)}
    for c in c_ls:
        d[c] = {'nan_values': nan_values(df[c])}
        dfc = df[c].dropna()
        m = mean(dfc)
        d[c]['mean'] = m
        d[c]['min'] = dfc.min()
        d[c]['max'] = dfc.max()
        d[c]['st_dev'] = st_dev(dfc, m)
        d[c]['st_dev_bessel'] = bessel_st_dev(dfc)

    for i in range(len(c_ls)):
        cx = c_ls[i]
        X = df[cx].dropna()
        mx = d[cx]['mean']
        for cy in c_ls[i:]:
            Y = df[cy].dropna()
            my = d[cy]['mean']
            d[cx][cy]['covariance'] = covariance(X, Y, mx, my)
            d[cx][cy]['covariance'] = covariance(X, Y, mx, my)

    #    mx = X.sum()/len(X)
    #     my =

    # def correlation(X,Y):
    #     {\displaystyle \operatorname {cov} (X,Y)=\operatorname {\mathbb {E} } [(X-\mu _{X})(Y-\mu _{Y})],}
    # the formula for
    # �\rho  can also be written as

    # �
    # �
    # ,
    # �
    # =
    # �
    # ⁡
    # [
    # (
    # �
    # −
    # �
    # �
    # )
    # (
    # �
    # −
    # �
    # �
    # )
    # ]
    # �
    # �
    # �
    # �
    # {\displaystyle \rho _{X,Y}={\frac {\operatorname {\mathbb {E} } [(X-\mu _{X})(Y-\mu _{Y})]}{\sigma _{X}\sigma _{Y}}}}
    # where

    return d
