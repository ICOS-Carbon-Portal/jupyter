# We use a specific hash since :latest has broken spuriously in the past.
# https://hub.docker.com/r/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 2021-01-20.
FROM jupyter/datascience-notebook@sha256:ed6c44b7b513783e541e251fa057ced63e91887179c16ae5c535fe103c86c3f4

# Experimental, use mamba.
# https://medium.com/@QuantStack/open-software-packaging-for-science-61cecee7fc23
RUN conda install -y mamba -c conda-forge && conda clean -qafy

RUN mamba install -qy                                                          \
        basemap basemap-data-hires cartopy geoviews holoviews panel datashader \
        hvplot param cdo python-cdo netcdf4 geopandas mpld3 pscript ipyleaflet \
        netcdf-fortran sparqlwrapper xarray shapely folium qgrid               \
        && mamba clean -qafy

# this is for the visual debugger in JupyterLab
RUN mamba install -qy xeus-python && mamba clean -qafy

# install the standard notebook extensions
# and activate the configurator
RUN mamba install -qy -c conda-forge jupyter_contrib_nbextensions
RUN jupyter nbextensions_configurator enable

# patch the default configuration for toc, 
# such that headers are NOT numbered by default
# and activate the extension

COPY nbextensionDefault/*.diff /tmp/
RUN patch /opt/conda/share/jupyter/nbextensions/toc2/toc2.yaml /tmp/toc2.yaml.diff
RUN patch /opt/conda/share/jupyter/nbextensions/toc2/toc2.js /tmp/toc2.js.diff
RUN jupyter nbextension enable toc2/main


RUN pip install pangaeapy
RUN pip install jupyter_module_loader

# update jupyter lab and rebuild
RUN jupyter labextension install @jupyterlab/debugger --no-build
RUN jupyter labextension install @lckr/jupyterlab_variableinspector --no-build
RUN jupyter labextension install qgrid2 --no-build
RUN jupyter lab build

WORKDIR /home/jovyan

# This directory is added by jupyter/base-notebook, "for backwards
# compatibility", but we don't need it.
RUN rmdir work

# This package, and the following notebook directories, are the stuff that
# changes most often, so we add them last.
RUN pip install icoscp --no-cache-dir
