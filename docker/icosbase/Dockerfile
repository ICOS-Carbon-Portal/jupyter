# We use a specific hash since :latest has broken spuriously in the
# past.
# https://hub.docker.com/r/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 26-08-2022.
#FROM jupyter/datascience-notebook@sha256:08677b8b71501eceb37cbd12f1fe0d5a80b3fe3e1b8caa2cbdd8bcd37429caaa
# This hash is jupyter/datascience-notebook:latest on 04-10-2022.
FROM jupyter/datascience-notebook@sha256:731da3b2844e168d677e622d6ce127e790117e291c57933deefd93bc5f79217d

# Remove the default xetex LaTeX installation of jupyter-lab and
# install the full latest LaTeX version. It takes about 45 minutes to
# install it, so be patient.
# Check links below to find which engine is used by default in jupyter
# notebooks to process TeX documents. Remember, minimal-notebook is
# included in datascience-notebook.
# https://github.com/jupyter/docker-stacks/blob/main/minimal-notebook/Dockerfile
# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-datascience-notebook
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

# This directory is added by jupyter/base-notebook, for backwards
# compatibility, but we don't need it.
WORKDIR /home/jovyan
RUN rmdir work

# Experimental, use mamba.
# https://medium.com/@QuantStack/open-software-packaging-for-science-61cecee7fc23
RUN conda install --yes mamba --channel conda-forge \
    && conda clean --quiet --all --force-pkgs-dirs --yes

# Install required packages.
RUN mamba install --quiet --yes \
    basemap=1.3.4 basemap-data-hires=1.3.2 \
    cartopy=0.21.0 cdo=2.0.5 \
    datashader=0.14.2 \
    folium=0.13.0 \
    geopandas=0.11.1 geoviews=1.9.5 gmt=6.4.0 \
    holoviews=1.15.1 hvplot=0.8.1 \
    ipyleaflet=0.17.1 \
    kml2geojson=5.1.0 \
    mpld3=0.5.8 \
    nco=5.1.0 netcdf4=1.5.8 netcdf-fortran=4.6.0 \
    openpyxl=3.0.10  \
    panel=0.14.0 papermill=2.3.4 param=1.12.2 plotly=5.10.0 pscript=0.7.7 pygmt=0.7.0 pypdf2=2.10.8 python-cdo=1.5.6 \
    s3fs=2022.10.0 shapely=1.8.4 \
    xarray=2022.9.0 \
    zarr=2.13.3 \
    && mamba clean --quiet --all --force-pkgs-dirs --yes

# Install this extension because it is needed for the qgrid extension
# installation.
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build
# Before installing the qgrid extension make sure you have installed
# the qgrid library. In this current jupyter/datascience-notebook image
# the qgrid library is already included, thus there is no need to
# reinstall it.
# Install qgrid extension.
RUN jupyter labextension install @j123npm/qgrid2@1.1.4 --no-build
# Rebuild jupyter lab.
RUN jupyter lab build

# Additional python modules, not available using mamba.
RUN pip install --quiet \
    jupyter-module-loader==0.0.1  \
    pangaeapy==1.0.6 \
    qgrid==1.3.1 \
    simplification==0.6.1 \
    # Version of nersc-refresh-announcements is 0.1.0.
    git+https://github.com/NERSC/nersc-refresh-announcements.git
# Override configuration for jupyter lab settings.
COPY overrides.json /opt/conda/share/jupyter/lab/settings/.
# Keep this in a separate line. It's the only library that changes
# frequently and the new docker image will build faster.
# Update version number according to latest release.
# RUN pip install --quiet icoscp==0.1.16
RUN pip install git+https://github.com/icos-carbon-portal/pylib.git@107_update_stationdata_sparql
