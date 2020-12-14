# We use a specific hash since :latest has broken spuriously in the past.
# https://hub.docker.com/layers/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 2020-11-13.
FROM jupyter/datascience-notebook@sha256:0d04ff6948f8e798fa1e774e09dbdb4f2cd9673a1e548452a63e7f66fa912d4a

# Trying to install all of these at once sometimes causes conda to crash.
RUN conda install -y basemap basemap-data-hires    && conda clean -afy
RUN conda install -y cartopy geoviews holoviews    && conda clean -afy
RUN conda install -y panel datashader hvplot param && conda clean -afy
RUN conda install -y cdo python-cdo netcdf4        && conda clean -afy
RUN conda install -y geopandas mpld3 pscript       && conda clean -afy
RUN conda install -y ipyleaflet netcdf-fortran     && conda clean -afy
RUN conda install -y sparqlwrapper xarray          && conda clean -afy
RUN conda install -y shapely folium                && conda clean -afy
RUN conda install -y qgrid                         && conda clean -afy

# this is for the visual debugger in JupyterLab
RUN conda install -y xeus-python                   && conda clean -afy

# install the standard notebook extenstions
# and activate the configuratore
RUN conda install -c conda-forge jupyter_contrib_nbextensions
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
