#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    The reason for IcosFrame is to create an ICOS timeseries object
    that works like a pandas dataframe and contains simple methods 
    to retrieve metadata of the object.
    
    Note: Not `all` manipulation properties have been tested and 
          some parameters will not work. 
          An example is the inplace flag in 
          `df.set_index('TIMESTAMP', inplace=True)`
    
    Method
    ------
    IcosFrame.trim_icos_meta(meta_dict: dict = None, 
                             columns: list = None,
                             keep_keys: bool = False) -> dict
    
    Properties
    ----------
    icos_meta -> dict
    icos_accessUrl -> str
    icos_pid -> str
    icos_previousVersion -> str
    icos_station_name -> str
    icos_station_id -> str
    icos_station_uri -> str
    icos_product -> str
    icos_citationBibTex -> str
    icos_citationRis -> str
    icos_citationString -> str
    icos_title -> str
    icos_columns -> dict
    icos_var_unit_ls -> list
    
    Examples
    --------
    >>> ### 1. Parse some ICOS metadata
    >>> from icoscp.cpb.dobj import Dobj
    >>> pid = "11676/10yUST7NRURFohvnTEGnvi4J"
    >>> do = Dobj(pid)
    >>> my_meta = do.meta
    >>> IcosFrame.trim_icos_meta(my_meta)
{'accessUrl': 'https://data.icos-cp.eu/objects/10yUST7NRURFohvnTEGnvi4J',
 'pid': '11676/10yUST7NRURFohvnTEGnvi4J',
 'previousVersion': 'https://meta.icos-cp.eu/objects/k-o5CPaWGi1YHiFS1uje-3RQ',
 'stationName': 'Lamasquere',
 'stationId': 'FR-Lam',
 ....}
    
    >>> ### 2. Create an IcosFrame object 
    >>> # Here we fetch some ETC NRT Fluxes data from Lamasquere
    >>> from icoscp.cpb.dobj import Dobj
    >>> pid = "11676/10yUST7NRURFohvnTEGnvi4J"
    >>> do = Dobj(pid)
    >>> pandas_df = do.data
    >>> meta =do.meta
    >>> df = IcosFrame(df, icos_meta = meta)
    
    >>> ### 2.1 Print the data
    >>> df 
             CO2    FC          H  ...  USTAR  W_SIGMA     ZL
0            NaN   NaN        NaN  ...    NaN      NaN    NaN
1     406.459991  2.86 -21.379999  ...  0.117     0.22  0.278
2     406.390015  2.16 -16.139999  ...  0.125     0.20  0.173
3     413.679993  3.73 -11.630000  ...  0.079     0.11  0.490
4     420.019989  6.49 -13.910000  ...  0.095     0.13  0.336
         ...   ...        ...  ...    ...      ...    ...
6524  407.700012  0.85 -16.030001  ...  0.098     0.16  0.500
6525  408.160004  1.69 -26.209999  ...  0.086     0.17  1.230
6526  408.010010  1.61 -39.540001  ...  0.159     0.22  0.292
6527  407.619995  0.91 -25.420000  ...  0.132     0.23  0.325
6528  408.480011  1.36 -24.889999  ...  0.111     0.19  0.533

[6529 rows x 16 columns]

    >>> ### 2.2 Print some meta data
    >>> print(df.icos_station_name
              df.icos_station_id,
              df.icos_product)
Lamasquere ETC FR-Lam NRT Fluxes 

    >>> ### 2.3. Get a list of variable and units
    >>> df.icos_var_unit_ls
[('TIMESTAMP', 'No unit'),
 ('TIMESTAMP_END', 'No unit'),
 ('FC', 'µmol m-2 s-1'),
 ('H', 'W m-2'),
 ('H2O', 'mmol mol-1'),
 ('LE', 'W m-2'),
 ('SC', 'µmol m-2 s-1'),
 ('TAU', 'kg m-1 s-2'),
 ('USTAR', 'm s-1'),
 ('W_SIGMA', 'm s-1'),
 ('ZL', 'No unit'),
 ('NEE', 'µmol m-2 s-1'),
 ('CO2', 'µmol mol-1'),
 ('NEE_UNCLEANED', 'µmol m-2 s-1'),
 ('LE_UNCLEANED', 'W m-2'),
 ('H_UNCLEANED', 'W m-2')]

    >>> ### 2.4. Fetch all stored meta (smaller than in do.meta)
    >>> df.icos_meta    
{'accessUrl': 'https://data.icos-cp.eu/objects/10yUST7NRURFohvnTEGnvi4J',
 'pid': '11676/10yUST7NRURFohvnTEGnvi4J',
 'previousVersion': 'https://meta.icos-cp.eu/objects/k-o5CPaWGi1YHiFS1uje-3RQ',
 'station_name': 'Lamasquere',
 'stationId': 'FR-Lam',
 'product': 'ETC NRT Fluxes',
 'citationBibTex': '@mis...
 ...
    
    >>> ### 3. Create a subframe of the dataframe df 
    >>> ###    with intact df.
    >>> df2 = df[['SC','CO2']]
    >>> df2 
        SC         CO2
0      NaN         NaN
1      NaN  406.459991
2     0.00  406.390015
3     0.49  413.679993
4     0.43  420.019989
   ...         ...
6524  0.06  407.700012
6525  0.03  408.160004
6526 -0.01  408.010010
6527 -0.03  407.619995
6528  0.06  408.480011

[6529 rows x 2 columns]

    >>> ### 3.1 Check variables and units of the subframe
    >>> df2.icos_var_unit_ls
[('SC', 'µmol m-2 s-1'), ('CO2', 'µmol mol-1')]
    
    df.CO2
    >>> df2.icos_var_unit_ls
    >>>
    
    
    >>> ### 4. Look at a column of df (a pandas Series object) 
    >>> ###    df will stay intact.
    >>> df3 = df.CO2
    >>> df3 
             CO2
0            NaN
1     406.459991
2     406.390015
3     413.679993
4     420.019989
         ...
6524  407.700012
6525  408.160004
6526  408.010010
6527  407.619995
6528  408.480011

[6529 rows x 1 columns]    

    >>> ### 4.1 Check the meta of df3
    >>> df3.icos_meta
{'accessUrl': 'https://data.icos-cp.eu/objects/10yUST7NRURFohvnTEGnvi4J',
 'pid': '11676/10yUST7NRURFohvnTEGnvi4J',
 'previousVersion': 'https://meta.icos-cp.eu/objects/k-o5CPaWGi1YHiFS1uje-3RQ',
 'station_name': 'Lamasquere',
 'stationId_id': 'FR-Lam',
 'product': 'ETC NRT Fluxes',
 'citationBibTex': '@misc{https://hdl.handle.net/11676/10yUST7NRURFohvnTEGnvi4J,
 \r\n  author={Brut, Aurore and Tallec, Tiphaine and Granouillac, Franck and
 Zawilski, Bartosz and Ceschia, Eric},\r\n  title={ETC NRT Fluxes, Lamasquere,
 2022-09-30–2023-02-13},\r\n  year={2023},\r\n
 url={https://hdl.handle.net/11676/10yUST7NRURFohvnTEGnvi4J},\r\n
 publisher={Ecosystem Thematic Centre},\r\n
 copyright={http://meta.icos-cp.eu/ontologies/cpmeta/icosLicence},\r\n
 pid={11676/10yUST7NRURFohvnTEGnvi4J}\r\n}',
 'citationRis': 'TY - DATA\r\nT1 - ETC NRT Fluxes, Lamasquere,
 2022-09-30–2023-02-13\r\nID - 11676/10yUST7NRURFohvnTEGnvi4J\r\nPY - 2023\r\nUR -
 https://hdl.handle.net/11676/10yUST7NRURFohvnTEGnvi4J\r\nPB - Ecosystem Thematic
 Centre\r\nAU - Brut, Aurore\r\nAU - Tallec, Tiphaine\r\nAU - Granouillac,
 Franck\r\nAU - Zawilski, Bartosz\r\nAU - Ceschia, Eric\r\nER - ',
 'citationString': 'Brut, A., Tallec, T., Granouillac, F., Zawilski, B., Ceschia,
 E. (2023). ETC NRT Fluxes, Lamasquere, 2022-09-30–2023-02-13, ICOS RI,
 https://hdl.handle.net/11676/10yUST7NRURFohvnTEGnvi4J',
 'title': 'ETC NRT Fluxes, Lamasquere, 2022-09-30–2023-02-13',
 'columns': {'H2O': {'label': 'Portion',
   'name': 'H2o molar fraction',
   'unit': 'mmol mol-1',
   'comment': 'Magnitude of a part of a whole. Can be measured in percent,
   or be a number between 0 and maximum (inclusive).'},
  'CO2': {'label': 'Portion',
   'name': 'Co2 mixing ratio (wet mole fraction)',
   'unit': 'µmol mol-1',
   'comment': 'Magnitude of a part of a whole. Can be measured in percent,
   or be a number between 0 and maximum (inclusive).'}}}

"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import pandas as pd
import copy

    
class IcosFrame(pd.DataFrame):
    @staticmethod
    def trim_icos_meta(dobj_meta: dict or list[dict] = None,
                       columns: str or list[str] = None,
                       keep_keys: bool = False) -> dict:
        """
        Returns a flattened dictionary with metadata of an
        ICOS digital object.

        Parameters
        ----------
        dobj_meta: dict or list[dict]
            - if a dict: Either `dobj_meta` is the metadata dictionary of an ICOS
            digital object (for details see the property meta of the
            class Dobj in icoscp.cpb.dobj), it can also be the metadata
            of a IcosFrame object.
            - if a list of dicts, each dict are as above. In this case some
            icos_properties will return lists. Instead of strings

        columns: str or list[str] (optional)
            - If `columns` is a string it will be converted to a list.
            - If `columns` is a list the list represent the standard ICOS
            timeseries column names (even though these might have been
            changed).
            - This will only affect the values of keys 'columns' and
            'varUnitList'.
            - If not provided all columns will be retrieved.

        keep_keys: bool (default False)
            If `keep_keys` is `True`, all keys of `dobj_meta` will
            be perserved.

        Returns
        -------
        dict
            The default keys are
            'accessUrl', 'pid', 'previousVersion', 'citationBibTex',
            'citationRis', 'citationString', 'stationName',
            'stationId', 'product', 'title', 'columns', 'varUnitList'

        That the method is `static` means that it will stay in RAM
        as long as the client session lasts. The user can access the
        method without creating in instance of the class.

        Examples
        --------
        >>> pid = 'https://meta.icos-cp.eu/objects/shvxQF02RVZRixeYHn9CCTFP'
        >>> meta = Dobj(pid).meta
        >>> mini_meta = IcosFrame.trim_icos_meta(meta)
        >>> mini_meta['stationId']
        'SE-Sto'
        >>> mini_meta['varUnitList']
        [('TIMESTAMP', 'No unit'),
         ('TIMESTAMP_END', 'No unit'),
         ('FC', 'µmol m-2 s-1'),
         ('H', 'W m-2'),
         ('H2O', 'mmol mol-1'),
         ('LE', 'W m-2'),
         ('SC', 'µmol m-2 s-1'),
         ('TAU', 'kg m-1 s-2'),
         ('USTAR', 'm s-1'),
         ('W_SIGMA', 'm s-1'),
         ('ZL', 'No unit'),
         ('NEE', 'µmol m-2 s-1'),
         ('CO2', 'µmol mol-1'),
         ('NEE_UNCLEANED', 'µmol m-2 s-1'),
         ('LE_UNCLEANED', 'W m-2'),
         ('H_UNCLEANED', 'W m-2')]
        >>> co2 = IcosFrame.trim_icos_meta(meta, 'CO2')
        >>> co2['varUnitList']
        [('CO2', 'µmol mol-1')]
        """
        m = dict()

        if isinstance(dobj_meta, list):
            meta_ls = dobj_meta
        elif isinstance(dobj_meta, dict):
            meta_ls = [dobj_meta]
        else:
            return m

        if columns:
            if isinstance(columns, list):
                col_ls = columns
            elif isinstance(columns, str):
                col_ls = [columns]
            else:
                col_ls = []
        else:
            col_ls = []

        nn = len(meta_ls)

        return_meta = {}
        for i in range(nn):
            # We don't want to change data where the meta_data came from
            d = copy.deepcopy(meta_ls[i])

            if keep_keys:
                m = copy.deepcopy(d)

            keys = ['accessUrl', 'pid', 'previousVersion', 'citationBibTex',
                    'citationRis', 'citationString', 'stationName',
                    'stationId', 'uri', 'product', 'title', 'columns',
                    'varUnitList']

            for k in keys:
                m[k] = d.pop(k, None)

            if not (m['stationName'] and m['stationId'] and m['uri']):
                try:
                    stn_data = d['specificInfo']['acquisition']['station']
                except:
                    stn_data = None

                if stn_data and not m['stationName']:
                    try:
                        m['stationName'] = stn_data['org']['name']
                    except:
                        pass
                if stn_data and not m['stationId']:
                    try:
                        m['stationId'] = stn_data['id']
                    except:
                        pass
                if stn_data and not m['uri']:
                    try:
                        m['uri'] = stn_data['org']['self']['uri']
                    except:
                        pass
            if not m['product']:
                try:
                    m['product'] = d['specification']['self']['label']
                except:
                    pass
            if not m['citationBibTex']:
                try:
                    m['citationBibTex'] = d['references']['citationBibTex']
                except:
                    pass
            if not m['citationRis']:
                try:
                    m['citationRis'] = d['references']['citationRis']
                except:
                    pass
            if not m['citationString']:
                try:
                    m['citationString'] = d['references']['citationString']
                except:
                    pass
            if not m['title']:
                try:
                    m['title'] = d['references']['title']
                except:
                    pass

            if not m['columns']:
                col_d = {}
                if 'specificInfo' in d.keys():
                    try:
                        data_col_ls = d['specificInfo']['columns']
                    except:
                        data_col_ls = []
                    if data_col_ls:
                        for col in data_col_ls:
                            c = col['label']
                            col_d[c] = {}
                            try:
                                label = col['valueType']['quantityKind']['label']
                                col_d[c]['label'] = label[0].upper() + label[
                                                                       1:].lower()
                            except:
                                col_d[c]['label'] = 'No label'
                            try:
                                name = col['valueType']['self']['label']
                                col_d[c]['name'] = name[0].upper() + \
                                                   name[1:].lower()
                            except:
                                col_d[c]['name'] = 'No name'
                            try:
                                col_d[c]['unit'] = col['valueType']['unit']
                            except:
                                col_d[c]['unit'] = 'Unitless'
                            try:
                                comment_ls = col['valueType']['quantityKind'][
                                    'comments']
                                comments = ' '.join(comment_ls)
                                col_d[c]['comment'] = "{0}{1}".format(
                                    comments[0].upper(), comments[1:])
                            except:
                                col_d[c]['comment'] = ''
                if col_d:
                    m['columns'] = col_d

            if 'columns' in m.keys() and isinstance(m['columns'], dict):
                if col_ls:
                    for k in (m['columns'].copy()).keys():
                        if k not in col_ls:
                            m['columns'].pop(k)
                var_unit_ls = []
                for col_name, col_meta in m['columns'].items():
                    var_unit_ls.append((col_name, col_meta['unit']))
                m['varUnitList'] = var_unit_ls
            if nn == 1:
                return_meta = m
            else:
                return_meta[i] = m

                # set keys to lists
                for k, v in m.items():
                    if k in return_meta.keys():
                        if k == 'varUnitList':
                            return_meta[k] = return_meta[k] + v
                        else:
                            return_meta[k].append(v)
                    elif k == 'varUnitList':
                        return_meta[k] = v
                    else:
                        return_meta[k] = [v]
        # finally we reset the order of varUnitList, and remove duplicates
        if col_ls:
            return_meta['varUnitList'] = [(c, u) for c in col_ls
                                          for v, u in
                                          set(return_meta['varUnitList'])
                                          if c == v]
        return return_meta

    _icos_kwargs_keys = ['icos_meta', 'icos_columns', 'icos_keep_keys']
    # This is needed for pandas to accept the property
    _metadata = ['_icos_meta']

    def __init__(self, *args, **kwargs):
        """
        To create an IcosFrame object use the kwargs keys
        'icos_meta', 'icos_columns', 'icos_keep_keys'
        """
        local_kwargs = {}
        for k in IcosFrame._icos_kwargs_keys:
            v = kwargs.pop(k, None)
            if v:
                local_kwargs[k] = v

        meta = local_kwargs.get('icos_meta', None)
        cols = local_kwargs.get('icos_columns', None)

        if isinstance(cols, list) and not isinstance(meta, list):
            kwargs['columns'] = cols

        copy_attrs = None
        if len(args) == 1:
            if isinstance(args[0], IcosFrame):
                copy_attrs = args[0]._get_attrs()
                pandas_df = pd.DataFrame(args[0])
                args = pandas_df,
    
        super(IcosFrame, self).__init__(*args, **kwargs)

        if copy_attrs:
            self._set_attrs(**copy_attrs)
        
        if local_kwargs:
            self._set_attrs(**local_kwargs)

    def __getitem__(self, key):
        if isinstance(self, IcosFrame):
            # We need to override pandas __getitem__ and 
            # take a deepcopy of the ICOS meta in order to 
            # preserve df for example when we call for a 
            # column like in df.CO2 
            meta = copy.deepcopy(getattr(self, '_icos_meta'))
            pandas_df = super(IcosFrame, self).__getitem__(key)
            icos_df = IcosFrame(pandas_df,
                                icos_meta=meta)
            return icos_df

    def _get_attrs(self):
        # Returns a dict with IcosFrame attributes of self
        d = {}
        for attr in self._metadata:
            if attr == '_icos_meta':
                self_meta = getattr(self, attr, None) 
                d['icos_meta'] = IcosFrame.trim_icos_meta(self_meta)
            else: 
                val = getattr(self, attr, None)
                d[attr] = val
        return d

    def _copy_attrs(self, df):
        # copy metadata from self to df.
        for attr in self._metadata:
            if attr == '_icos_meta':
                self_meta = getattr(self, attr, None)
                copied_meta = self_meta
                cols = list(df.columns)
                parsed_meta = IcosFrame.trim_icos_meta(copied_meta, cols)
                df.__dict__[attr] = parsed_meta  
            else: 
                val = getattr(self, attr, None)
                df.__dict__[attr] = val

    def _set_attrs(self, **kwargs):
        # This is where we set the metadata
        cols = kwargs.pop('icos_columns', None)
        keep = kwargs.pop('icos_keep_keys', False)
        for k, v in kwargs.items():
            if k == 'icos_meta':

                if cols is None:
                    cols = list(self.columns)
                parsed_meta = IcosFrame.trim_icos_meta(dobj_meta=v,
                                                       columns=cols,
                                                       keep_keys=keep)
                setattr(self, '_icos_meta', parsed_meta)
            else:
                setattr(self, k, v)

    def set_index(self, *args, **kwargs):
        # keys,
        # drop: bool = True,
        # append: bool = False,
        # inplace: bool = False,
        # verify_integrity: bool = False,  ):
        self_attrs = self._get_attrs()
        
        inplace = kwargs.get('inplace', False)
        if inplace:
            raise AttributeError(f"The attribute '{inplace}' is not" +
                                 "implemented for IcosFrame")
        else:
            
            pandas_df = super(IcosFrame, self).set_index(*args, **kwargs)
            cols = list(pandas_df.columns)
            icos_df = IcosFrame(pandas_df,
                                icos_columns=cols,
                                **self_attrs)
        return icos_df

    @property
    def icos_meta(self) -> dict:
        try:
            meta = self._icos_meta
        except:
            meta = ''
        return meta
    
    @property
    def icos_accessUrl(self) -> str:
        try:
            accessUrl = self._icos_meta['accessUrl']
        except:
            accessUrl = ''
        return accessUrl

    @property
    def icos_pid(self) -> str:
        try:
            pid = self._icos_meta['pid']
        except:
            pid = ''
        return pid
    
    @property
    def icos_previousVersion(self) -> str:
        try:
            previousVersion = self._icos_meta['previousVersion']
        except:
            previousVersion = ''
        return previousVersion
    
    @property
    def icos_station_name(self) -> str:
        try:
            name = self._icos_meta['stationName']
        except:
            name = ''
        return name
    
    @property
    def icos_station_id(self) -> str:
        try:
            st_id = self._icos_meta['stationId']        
        except:
            st_id = ''
        return st_id

    @property
    def icos_station_uri(self) -> str:
        try:
            st_uri = self._icos_meta['uri']
        except:
            st_uri = ''
        return st_uri

    @property
    def icos_product(self) -> str:
        try:
            product = self._icos_meta['product']
        except:
            product = ''
        return product

    @property
    def icos_citationBibTex(self) -> str:
        try:
            citation = self._icos_meta['citationBibTex']
        except:
            citation = ''
        return citation
    
    @property
    def icos_citationRis(self) -> str:
        try:
            citation = self._icos_meta['citationRis']
        except:
            citation = ''
        return citation

    @property
    def icos_citationString(self) -> str:
        try:
            citation = self._icos_meta['citationString']
        except:
            citation = ''
        return citation

    @property
    def icos_title(self) -> str:
        try:
            title = self._icos_meta['title']
        except:
            title = ''
        return title

    @property
    def icos_columns(self) -> dict:
        try:
            columns = self._icos_meta['columns']
        except:
            columns = {}
        return columns

    @property
    def icos_var_unit_ls(self) -> list:
        try:
            var_unit_ls = self._icos_meta['varUnitList']
        except:
            var_unit_ls = []
        return var_unit_ls
