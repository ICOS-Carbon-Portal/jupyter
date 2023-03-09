# Standard library imports.
import os

# Related third party imports.
from icoscp.sparql.runsparql import RunSparql

# Local application/library specific imports.
from modules.sparql_queries import q_find_data_object_from_name, q_find_radon_maps


def get_file_path(file_name):
    """Get the file's path on the carbon protal server."""
    # Path to netcdf files on the carbon portal server.
    path_to_netcdf = '/data/dataAppStorage/netcdf/'
    file_info = [None, None]
    # Find the object's landing page using its file name.
    d_result = RunSparql(sparql_query=q_find_data_object_from_name(file_name), output_format='pandas').run()
    if not d_result.empty:
        # Extract the object's pid.
        pid = d_result['dobj'][0].split('/')[-1]
        # Construct the file's path on the carbon portal server.
        path_on_server = f'{path_to_netcdf}{pid}'
        if not os.path.exists(path_on_server):
            print(f'File {file_path_on_server} does not exist on Carbon Portal server.')
        else:
            file_info = [file_name, path_on_server]
    return file_info


def get_radon_maps(outfmt: str = 'list'):
    """Get a dictionary or list of radon maps."""
    # Query all radon flux maps to a dataframe.
    df_radon_maps = RunSparql(sparql_query=q_find_radon_maps(), output_format='pandas').run()
    # Extract maps' file names.
    file_names = df_radon_maps['fileName'].to_list()
    # For each map, extract its pid and find its path on the carbon 
    # portal server.
    maps = None
    if outfmt == 'list':
        maps = list()
    elif outfmt == 'dict':
        maps = dict()
    for map_name in file_names:
        file_info = get_file_path(file_name=map_name)
        if isinstance(maps, list):
            maps.append(file_info[1])
        elif isinstance(maps, dict):
            maps.setdefault(*file_info)
    return maps
