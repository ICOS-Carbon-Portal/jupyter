# We use a specific hash since :latest has broken spuriously in the past.
# https://hub.docker.com/r/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 2021-01-12.
FROM jupyter/datascience-notebook@sha256:a7cd0b731489799fc8cc7b451a8a3d6ee6675691f9658a4b0ff056f9c0f9271b

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

# install the standard notebook extenstions
# and activate the configuratore
RUN mamba install -qy -c conda-forge jupyter_contrib_nbextensions
RUN jupyter nbextensions_configurator enable

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

# 1000:100 is jovyan:users
ADD --chown=1000:100 education ./education
ADD --chown=1000:100 icos_jupyter_notebooks ./icos_jupyter_notebooks
ADD --chown=1000:100 project_jupyter_notebooks ./project_jupyter_notebooks
ADD --chown=1000:100 introduction ./introduction
ADD --chown=1000:100 pylib_examples ./pylib_examples
