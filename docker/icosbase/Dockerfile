# We use a specific hash since :latest has broken spuriously in the
# past.
# https://hub.docker.com/r/jupyter/datascience-notebook
# This hash is jupyter/datascience-notebook:latest on 2022-10-04.
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
# RUN rm -rf /usr/share/texlive
RUN rm -rf /usr/share/texlive /opt/texlive /var/cache/texlive /tmp/texlive
# Add texlive2024 installer and unpack.
# http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN wget -O /tmp/install-tl-unx.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xf /tmp/install-tl-unx.tar.gz --strip-components=1 -C /tmp/
# Add profile and start intallation.
COPY Texlive2024/texlive.profile /tmp/.
RUN /tmp/install-tl --profile=/tmp/texlive.profile
# Export path to texlive2024.
ENV PATH="/usr/local/texlive/2024/bin/x86_64-linux:${PATH}"

RUN apt-get update
RUN apt-get install -y zip rsync

# Switch back to normal user.
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
COPY mamba_requirements.txt  mamba_requirements.txt
RUN mamba install --quiet --yes --file mamba_requirements.txt  \
    && mamba clean --quiet --all --force-pkgs-dirs --yes
RUN rm mamba_requirements.txt

# Install this extension because it is needed for the qgrid extension
# installation.
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build

# Install qgrid extension.
RUN jupyter labextension install @j123npm/qgrid2@1.1.4 --no-build
# Rebuild jupyter lab.
RUN jupyter lab build

# Additional python modules, not available using mamba.
RUN pip install uv==0.5.29
COPY pip_requirements.txt  pip_requirements.txt
RUN uv pip install --quiet --requirement pip_requirements.txt --system
RUN rm pip_requirements.txt

# Add env variable for PROJ (library used by cartopy and shapely).
ENV PROJ_LIB=/opt/conda/share/proj

# Override configuration for jupyter lab settings.
COPY overrides.json /opt/conda/share/jupyter/lab/settings/.

# Since icos-splash is just a repo, we retrieve a json objects that
# describes the "trunk" branch (SHA of the branch among other things),
# to force docker to re-build this step.
ADD https://api.github.com/repos/ZogopZ/icos-splash/git/refs/heads/trunk cache-bust
# Install jupyter-lab extension icos-splash, to modify the splash
# animation using the ICOS Carbon Portal logo.
RUN pip install git+https://github.com/ZogopZ/icos-splash.git
RUN rm cache-bust


# ---
# Keep this in a separate line. It's the only library that changes
# frequently and the new docker image will build faster.
# Update version number according to latest release.

# Install specific version.
RUN pip install --quiet icoscp_core==0.3.7
RUN pip install --quiet icoscp==0.2.2
RUN pip install --quiet icoscp_stilt==0.1.3
# RUN pip install --extra-index-url https://pypi.org/simple --quiet -i https://test.pypi.org/simple/ icoscp==0.2.0a2
# RUN pip install --extra-index-url https://pypi.org/simple --quiet -i https://test.pypi.org/simple/ icoscp_stilt==0.1.0a5

# Install from branch.
# This next line helps docker understand that there are changes in a
# branch and redo the pip install step. Otherwise docker sees no
# changes.
# ADD https://api.github.com/repos/ICOS-Carbon-Portal/pylib/git/refs/heads/master /tmp/cache-bust
# RUN pip install git+https://github.com/ICOS-Carbon-Portal/pylib.git@master
# ---

ENV PORTAL_DATA_PATH_ICOS="/data/dataAppStorage/"
ENV PORTAL_DATA_PATH_SITES="/data/dataAppStorage/"
ENV PORTAL_DATA_PATH_ICOSCITIES="/data/cities/dataAppStorage"
