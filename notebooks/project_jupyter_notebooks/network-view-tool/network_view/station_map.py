from icoscp.stilt import stiltstation
stilt_stations = stiltstation.find()
import pandas as pd
import folium

def create_stations_dfs():
    df_stilt_stations = pd.DataFrame(columns = ['id','name', 'lat', 'lon', 'country'])
    df_icos_stations = pd.DataFrame(columns = ['id','name', 'lat', 'lon', 'uri', 'country'])

    i_stilt = 0
    i_icos = 0 
    for key in list(stilt_stations.keys()):
        name = stilt_stations[key]['name']
        lat = stilt_stations[key]['lat']
        lon = stilt_stations[key]['lon']

        try:
            country = stilt_stations[key]['geoinfo']['name']['common']
        except:
            country = ''

        if stilt_stations[key]['icos']:

            try:
                uri= stilt_stations[key]['icos']['uri'][0]
            except:
                uri = ''

            df_icos_stations.loc[i_icos] = [key, name, lat, lon, uri, country]
            i_icos = i_icos + 1
        else:
            df_stilt_stations.loc[i_stilt] = [key, name, lat, lon, country]
            i_stilt = i_stilt + 1
            
    return df_stilt_stations, df_icos_stations 

def station_map():
    
    df_stilt_stations, df_icos_stations=  create_stations_dfs()
    
    m = folium.Map()
    light_tiles = folium.TileLayer(
        tiles='CartoDB positron',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        max_zoom=19,
        name='CartoDB positron',
        overlay = False,
        control=True,
    )
    m = folium.Map(tiles='CartoDB positron')
    dark_tiles = folium.TileLayer(
        tiles='CartoDB dark_matter',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        max_zoom=19,
        name='CartoDB dark matter',
        overlay = False,
        control=True
    ).add_to(m)
    satellite_tiles = folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = False,
        control = True
    ).add_to(m)

    icos_stations = folium.FeatureGroup('ICOS stations')
    for i, station in df_icos_stations.iterrows():
        folium.CircleMarker(
            [station.lat, station.lon],
            tooltip = station.id,
            popup = station['name'] + ', (' + station.country + '), <a href="' + station.uri + '" target="_blank">Data Landing Page</a>',
            fill_color = 'orange', fill_opacity=0.8, weight=1, color='#fff', radius=8
        ).add_to(icos_stations)

    stilt_stations = folium.FeatureGroup('STILT stations')
    for i, station in df_stilt_stations.iterrows():
        folium.CircleMarker(
            [station.lat, station.lon],
            tooltip = station.id,
            popup = station['name'] + ', (' + station.country + ')',
            fill_color = 'magenta', fill_opacity=0.6, weight=1, color='#fff', radius=8
        ).add_to(stilt_stations)

    icos_stations.add_to(m)
    stilt_stations.add_to(m)

    southwest_corner = [min(float(df_icos_stations.lat.min()), float(df_icos_stations.lat.min())), min(float(df_icos_stations.lon.min()), float(df_icos_stations.lon.min()))]
    northeast_corner = [max(float(df_icos_stations.lat.max()), float(df_icos_stations.lat.max())), max(float(df_icos_stations.lon.max()), float(df_icos_stations.lon.max()))]
    bounding_box = [southwest_corner, northeast_corner]
    m.fit_bounds(bounding_box)
    folium.LayerControl().add_to(m)
    
    return m
