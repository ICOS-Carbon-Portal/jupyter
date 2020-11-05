# We use a specific hash since :latest has broken spuriously in the past.
# https://hub.docker.com/r/jupyter/scipy-notebook/tags
# This hash is jupyter/scipy-notebook:latest on 2020-08-02.
FROM jupyter/scipy-notebook@sha256:e89b7047155fdf359152cf3fa34140e4ce8158d96eabb15fe42cc8cf587b6635

# Trying to install all of these at once sometimes causes conda to crash.
RUN conda install -y basemap basemap-data-hires    && conda clean -afy
RUN conda install -y cartopy geoviews holoviews    && conda clean -afy
RUN conda install -y panel datashader hvplot param && conda clean -afy
RUN conda install -y cdo python-cdo netcdf4        && conda clean -afy
RUN conda install -y geopandas mpld3 pscript       && conda clean -afy
RUN conda install -y ipyleaflet netcdf-fortran     && conda clean -afy
RUN conda install -y sparqlwrapper xarray          && conda clean -afy
RUN conda install -y shapely folium                && conda clean -afy

RUN pip install pangaeapy
RUN pip install jupyter_module_loader
RUN pip install qgrid

WORKDIR /home/jovyan

# This directory is added by jupyter/base-notebook, "for backwards
# compatibility", but we don't need it.
RUN rmdir work

# This package, and the following notebook directories, are the stuff that
# changes most often, so we add them last.
RUN pip install icoscp --upgrade

# 1000:100 is jovyan:users
ADD --chown=1000:100 education ./education
ADD --chown=1000:100 icos_jupyter_notebooks ./icos_jupyter_notebooks
ADD --chown=1000:100 project_jupyter_notebooks ./project_jupyter_notebooks
ADD --chown=1000:100 introduction ./introduction
ADD --chown=1000:100 pylib_examples ./pylib_examples
