# We use a specific hash since :latest has broken spuriously in the past.
# https://hub.docker.com/r/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 18-03-2022.
FROM jupyter/datascience-notebook@sha256:9e64f73a33a52533a5663c389052716775089aa0f0cfe6085f6833046cb83f9c
# -------------------------
# Remove the default xetex LaTeX installation of jupyter-lab and
# install the full latest LaTeX version. It takes about 45 minutes to
# install it, so be patient.

# Switch to root for texlive installation.
USER root
# Remove old texlive installation.
RUN rm -rf /usr/share/texlive
# Add texlive2021 installer and unpack.
# http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN wget -O /tmp/install-tl-unx.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xf /tmp/install-tl-unx.tar.gz --strip-components=1 -C /tmp/
# Add profile and start intallation.
COPY Texlive2021/texlive.profile /tmp/.
RUN /tmp/install-tl --profile=/tmp/texlive.profile
# Export path to texlive2021
ENV PATH="/usr/local/texlive/2021/bin/x86_64-linux:${PATH}"
# switch back to normal user
USER jovyan
# -------------------------

# Experimental, use mamba.
# https://medium.com/@QuantStack/open-software-packaging-for-science-61cecee7fc23
RUN conda install --yes mamba --channel conda-forge \
    && conda clean --quiet --all --force-pkgs-dirs --yes
# Install required packages
RUN mamba install --quiet --yes \
    basemap basemap-data-hires cartopy geoviews holoviews panel datashader hvplot param cdo \
    python-cdo netcdf4 geopandas mpld3 pscript ipyleaflet netcdf-fortran sparqlwrapper xarray \
    shapely folium qgrid zarr plotly nco qgrid xeus-python \
    && mamba clean --quiet --all --force-pkgs-dirs --yes

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


# Additional python modules, not available using mamba.
# - openpyxl: Pandas require openpyxl module to read excel files.
# - kml2geojson: Convert kml files to geojson.
# - simplification: simplify polygons.
RUN pip install --quiet pangaeapy jupyter-module-loader kml2geojson simplification openpyxl
# Keep this in a separate line. It's the only library that changes
# frequently and the new docker image will build faster.
# Update version number according to latest release.
RUN pip install --quiet icoscp==0.1.14

WORKDIR /home/jovyan

# This directory is added by jupyter/base-notebook, "for backwards
# compatibility", but we don't need it.
RUN rmdir work

# This package, and the following notebook directories, are the stuff that
# changes most often, so we add them last.
RUN pip install icoscp==0.1.14