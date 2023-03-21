#!/usr/bin/python

"""
    This auxiliary program is a datalayer to ingested/previewable
    data from ICOS Carbon Portal (https://data.icos-cp.eu/portal/).

    Public members
    --------------
    stations_df()   Holds a dataframe with stations and ids to the
                    products of the station.
    get_ts()        Returns a timeseries of
        + data()


    Examples
    --------
    >>> # Ex 1. Get a list of all AS-stations together with
    >>> # their level 2 products
    >>> from pi.icos_data import StationData
    >>> as_stations = StationData(theme='AS', level = '2')
    >>> df = as_stations.stations_df
    ...
    >>> # Ex 2. Get the timeseries and look up variables and units
    >>> ts_df = as_stations.icos_ts(pid = '11676/gzsZmFSwlOyPtBmCPzQXU9QY')
    >>> ts_df.icos_var_unit_ls

    ...
"""

import warnings

warnings.simplefilter("ignore", FutureWarning)

import pandas as pd
from icoscp.cpb.dobj import Dobj
from icoscp.station import station as st
from icoscp.sparql import sparqls, runsparql
from pi.icos_timeseries import IcosFrame


class StationData():

    def __init__(self, **configs):
        """
        Interface to ICOS stations and their data objects.

        Keys of configs
        ---------------
        theme: str
            Default is 'ES'. Possible values: 'AS','ES','OS'
        level: str
            Default is '1'. Possible values: '1','2'
        products: list of strings
            A list of ICOS products. If non-empty other products
            are skipped.
        debug: bool
            Default is False. If True, messages are printed.
        """

        self._attr = {}

        debug = configs.pop('debug', False)
        self['debug'] = debug if isinstance(debug, bool) else False

        theme = configs.pop('theme', None)
        theme = str(theme).upper()
        self['theme'] = theme if theme in ['AS', 'ES', 'OS'] else 'ES'

        level = configs.pop('level', None)
        level = str(level).upper()
        self['level'] = level if level in ['1', '2'] else '1'

        products = configs.pop('products', None)
        self['products'] = self.__valid_products(products)

        self['stations_df'] = self.__collect_stations()

    def __setattr__(self, key, value):
        if key != '_attr':
            return
        else:
            object.__setattr__(self, key, value)

    def __setitem__(self, key, value):
        if key in self._attr.keys() or \
                key not in ['debug', 'theme', 'level', 'products', 'stations_df']:
            return
        else:
            self._attr[key] = value

    def __getitem__(self, key):
        return self._attr[key]

    @property
    def theme(self):
        return self['theme']

    @property
    def level(self):
        return self['level']

    @property
    def debug(self):
        return self['debug']

    @property
    def products(self):
        return self['products']

    @property
    def stations_df(self):
        return self['stations_df']

    def __valid_products(self, products):
        """
        At this moment there is only a simple validation 
        for level 1 data of ICOS ES stations. These are
         'ETC NRT Fluxes', 
         'ETC NRT Meteo', 
         'ETC NRT Meteosens'
        The level 1 ES product 'ETC NRT AuxData' will not 
        be handled here, the reason is that none of the 
        variables therein are ingested into the ICOS carbon 
        portal. Instead, these are stored in a zipped csv file.                
        """

        if self.theme == 'ES' and self.level == '1':
            valid_products = ['ETC NRT Fluxes', 'ETC NRT Meteo',
                              'ETC NRT Meteosens']
            if products:
                product_ls = [x for x in products if x in valid_products]
            else:
                product_ls = valid_products
        else:
            product_ls = None

        return product_ls

    def __collect_stations(self):
        """
        Returns: pandas.DataFrame 
        By default the returned dataframe contain all 
        ICOS stations with products that match the theme,
        level and products in the instantiation.
        """

        # 1. We use the `icoscp.station` module to collect all ICOS
        # stations (with the chosen).
        if self.theme == 'ALL':
            stns_df = st.getIdList()
        else:
            stns_df = st.getIdList(theme=self.theme)

        # 2. Using the station uris we fetch the products of the stations,
        query = sparqls.stationData(stns_df.uri, self.level)
        prod_df = runsparql.RunSparql(sparql_query=query,
                                      output_format='pandas').run()

        # 3. Among the collected products, we will only consider some
        if self.products:
            prod_df = prod_df.loc[prod_df.specLabel.isin(self.products)]

        # 4. Next, we gather the data. The dataframe holding the products
        # have the station uri in the column `prod_df.station`, which we
        # will use to merge the products into a dataframe of stations
        # with products
        stns_and_prod_df = stns_df.merge(prod_df, how='inner',
                                         left_on='uri',
                                         right_on='station')

        # Finally, we remove all columns that we will not use, sort
        # the remaining df with respect to station name, specLabel, date 
        # remove and objects created.
        col_ls = ['id', 'name', 'specLabel',
                  'dobj', 'timeStart', 'timeEnd']
        sort_ls = ['name', 'specLabel', 'timeEnd']
        ascending_ls = [True, True, False]
        if self.theme == 'AS' or self.theme == 'ALL':
            # For atmospheric stations we
            # also need the sampling height.
            col_ls.append('samplingheight')
            sort_ls.insert(2, 'samplingheight')
            ascending_ls.insert(2, False)

        final_df = stns_and_prod_df[col_ls].copy()

        final_df.sort_values(by=sort_ls,
                             ascending=ascending_ls,
                             inplace=True,
                             ignore_index=True)

        return final_df

    def icos_product_meta(self, pid: str = None) -> dict:
        if not pid:
            return {}
        do = Dobj(pid)
        meta = do.meta
        parsed_meta = IcosFrame.trim_icos_meta(meta)
        column_meta = parsed_meta['columns']
        del do

        return column_meta

    def get_ts(self, pid: str = None, stn_id: str = None,
                stn_name: str = None, product: str = None,
                col_ls: list = None, **kwargs) -> IcosFrame:
        """
        Returns a pandas dataframe df with an ICOS timeseries
        and attached metadata (an instance of IcosFrame which
        inherits pandas dataframe).
        If no pid is given, the stations_df will be used as a
        lookup table and in case there are more than one matching
        product, the latest will be returned.

        Mandatory parameters
        --------------------
        pid or (stn_id and product) or (stn_name and product)

        Parameters
        ----------
        pid: str
            pid of an ICOS digital object.
        stn_id: str
            ICOS station id.
        stn_name: str
            ICOS station name
        product: str
            Name of a product of an ICOS station.
        col_ls: list of strings
            List of columns to retrieve. The column 'TIMESTAMP' 
            will be added if it is not in the list.
        
        Returns
        -------
        IcosFrame (see above)        
        """

        if pid:
            pass
        else:
            if isinstance(self.stations_df, pd.DataFrame):
                df = self.stations_df
                if stn_id and product:
                    row = df.loc[(df.id == stn_id) & (df.specLabel == product)]
                    pid = row.dobj.values[0]
                elif stn_name and product:
                    row = df.loc[(df.name == stn_name) & (df.specLabel == product)]
                    pid = row.dobj.values[0]
                else:
                    if debug:
                        print('Immature call of `StationData.get_ts`. ' +
                              f'\n{self.get_ts().__doc__}')
                    return
            else:
                return

        do = Dobj(pid)
        df = do.data
        meta = do.meta

        # Filter out columns
        if col_ls:
            if 'TIMESTAMP' not in col_ls:
                col_ls.append('TIMESTAMP')
            kwargs['icos_columns'] = col_ls

        kwargs['icos_meta'] = meta

        # Create timeseries and set metadata
        ts_df = IcosFrame(df, **kwargs)

        return ts_df

    @staticmethod
    def group_ts(var_tuple_ls: list = None,
                 start_date: str = None,
                 end_date: str = None) -> IcosFrame:
        """
        Returns a pandas dataframe df with an ICOS timeseries
        and attached metadata (an instance of IcosFrame which
        inherits pandas dataframe). In case there are more than
        one matching products, the latest will be returned.

        Parameters
        ----------
        var_tuple_ls: list of tuples
            Each tuple in the list is assumed to be of the form
                (<variable>, <pid>)
            where the <variable> belongs to the ICOS product/file with pid <pid>

        start_date: str
            Of the form 'YYYY-MM-DD'
        end_date: str
            Of the form 'YYYY-MM-DD'

        Returns
        -------
        IcosFrame (see above)
        """

        # 1. Before we merge the data we need to take care of the name and the
        #    order of the variables
        order_dict = {}
        original_columns = []
        for i in range(len(var_tuple_ls)):
            v, p = var_tuple_ls[i]
            original_columns.append(v)

            if p in order_dict.keys():
                order_dict[p]['cols'].append(v)
                order_dict[p]['compose_order'][i] = v
            else:
                order_dict[p] = {'cols': [v], 'compose_order': {i: v},
                                 'dobj': Dobj(p)}

        # 2. We might also have to rename duplicate variables.
        products = set()
        stations = set()
        if len(order_dict.keys()) > 1:
            # in this case we will rename columns
            for p in order_dict.keys():
                p_meta = IcosFrame.trim_icos_meta(order_dict[p]['dobj'].meta)
                order_dict[p]['meta'] = p_meta
                products.add(p_meta['product'])
                stations.add(p_meta['stationId'])
                order_dict[p]['product'] = p_meta['product']
                order_dict[p]['stn_id'] = p_meta['stationId']
        else:
            p_meta = IcosFrame.trim_icos_meta(order_dict[p]['dobj'].meta)
            order_dict[p]['meta'] = p_meta

        if len(products) > 1:
            for p in order_dict.keys():
                prod = order_dict[p]['product']
                order_dict[p]['rename_cols'] = {c: f'{prod}_{c}' for c in
                                                order_dict[p]['cols']}
        if len(stations) > 1:
            for p in order_dict.keys():
                stn_id = order_dict[p]['stn_id']
                if 'rename_cols' in order_dict[p].keys():
                    order_dict[p]['rename_cols'] = {c: f'{stn_id}_{v}'
                                                    for c, v in
                                                    order_dict[p][
                                                        'rename_cols'].items()}
                else:
                    order_dict[p]['rename_cols'] = {c: f'{stn_id}_{c}' for c in
                                                    order_dict[p]['cols']}

        # 3. Next, we gather the data in a dataframe and keep track on the order
        df_m = None
        total_col_order = {}
        for p in order_dict.keys():
            do = order_dict[p]['dobj']
            col_ls = order_dict[p]['cols'] + ['TIMESTAMP']
            df = do.data[col_ls]
            if 'rename_cols' in order_dict[p].keys():
                df.rename(columns=order_dict[p]['rename_cols'], inplace=True)
                total_col_order.update({i: order_dict[p]['rename_cols'].get(v)
                                        for i, v in
                                        order_dict[p]['compose_order'].items()})
            else:
                total_col_order.update(order_dict[p]['compose_order'])

            if df_m is None:
                df_m = df
            else:
                df_m = df_m.merge(df, how='outer', on='TIMESTAMP')

        # We use timestamp as index and restrict the set with respect to dates
        df_m.set_index(keys='TIMESTAMP', inplace=True)

        if start_date:
            df_m = df_m[start_date:]
        if end_date:
            df_m = df_m[:end_date]

        col_order = [total_col_order[i] for i in range(len(total_col_order))]
        df_m = df_m[col_order]

        # 5. Finally, we set the metadata using an IcosFrame
        meta_ls = [order_dict[p]['meta'] for p in order_dict.keys()]

        if len(order_dict.keys()) == 1:
            meta_ls = meta_ls.pop(0)

        df = IcosFrame(data=df_m, icos_meta=meta_ls,
                       icos_columns=original_columns)

        return df
