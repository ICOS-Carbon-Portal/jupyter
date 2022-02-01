# We use a specific hash since :latest has broken spuriously in the past.
# https://hub.docker.com/r/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 2021-01-28.
FROM jupyter/datascience-notebook@sha256:e6d5c7d595d25f6ec7a894d8fcc7cb4b542c28f65fb71cdf0cb9b77f0ce0ddd0

# -------------------------
# this block is added to the top of the Dockerfile
# because it takes about 45 minutes to install TL2020, so be patient.
# Install a full version of Texlive2020 (https://tug.org/texlive/)
# switch to root for texlive installation
USER root

# Remove old texlive installation
RUN rm -rf /usr/share/texlive

# Add texlive2020 installer and unpack
# http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz

RUN wget -O /tmp/install-tl-unx.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xf /tmp/install-tl-unx.tar.gz --strip-components=1 -C /tmp/

# add profile and start intallation

COPY Texlive2020/texlive.profile /tmp/.
RUN /tmp/install-tl --profile=/tmp/texlive.profile

# export path to texlive2020
ENV PATH="/usr/local/texlive/2020/bin/x86_64-linux:${PATH}"

# switch back to normal user
USER jovyan

# -------------------------

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

# update jupyter lab and rebuild
RUN jupyter labextension install @jupyterlab/debugger --no-build
RUN jupyter labextension install @lckr/jupyterlab_variableinspector --no-build
# jupter lab build fails with this base-notebook
#RUN jupyter labextension install qgrid2 --no-build
RUN jupyter lab build

RUN pip install pangaeapy
RUN pip install jupyter_module_loader

# convert kml files to geojson
RUN pip install kml2geojson

# simplify polygons 
RUN pip install simplification

WORKDIR /home/jovyan

# This directory is added by jupyter/base-notebook, "for backwards
# compatibility", but we don't need it.
RUN rmdir work

# This package, and the following notebook directories, are the stuff that
# changes most often, so we add them last.
RUN pip install icoscp==0.1.13


# -----start temp fix---2021-03-26 CD-------------------

# temporary fixes to the icos base image
# current version of jupyter/datascience-notebook
# has updated version of pandas which needs openpyxl to read excel files
RUN mamba install -qy openpyxl

# gdal 3.2.1 can't be loaded.. downgrade to last version we 
# know is working

RUN mamba install -qy gdal=3.1.4

# -----eof temp fix------------------------------------
