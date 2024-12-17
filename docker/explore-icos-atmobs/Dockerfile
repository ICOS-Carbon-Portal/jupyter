FROM jupyter/datascience-notebook@sha256:731da3b2844e168d677e622d6ce127e790117e291c57933deefd93bc5f79217d
# Change ownership to correctly mount the desired directories.
ADD --chown=1000:100 ./notebooks/explore-icos-atmobs/ /home/jovyan/
# This directory is added by jupyter/base-notebook, for backwards
# compatibility, but we don't need it.
RUN rm -r /home/jovyan/work
# Install required packages.
RUN pip install git+https://github.com/ZogopZ/icos-splash.git
RUN pip install --quiet icoscp_core==0.3.7 icoscp==0.2.2 pandas==1.3.5
ENV PORTAL_DATA_PATH_ICOS="/data/dataAppStorage/"
