# https://quay.io/repository/jupyter/datascience-notebook
# This hash is quay.io/jupyter/datascience-notebook:latest on 2026-03-18.
FROM quay.io/jupyter/datascience-notebook@sha256:8040395c8534cdf96388c20a85a2e89a259dbce057e67d6fd7577c2a9beea5c3

# Install system packages.
USER root
RUN apt-get update && apt-get install -y zip rsync curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /home/jovyan/.conda && \
    chown -R jovyan:users /home/jovyan && \
    chmod -R a+rwx /home/jovyan/.conda /opt/conda
USER jovyan
RUN rmdir /home/jovyan/work

# Install mamba packages.
COPY content/mamba_requirements.txt .
RUN mamba install --quiet --yes -c conda-forge --file mamba_requirements.txt \
    && mamba clean --quiet --all --force-pkgs-dirs --yes \
    && rm mamba_requirements.txt

# Install R packages not available on conda-forge.
RUN Rscript -e 'install.packages("DAAG", repos="https://cloud.r-project.org")'

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /usr/local/bin/

# Install pip packages.
COPY content/pip_requirements.txt .
RUN uv pip install --quiet --requirement pip_requirements.txt --system \
    && rm pip_requirements.txt

# Install ICOS JupyterLab extensions.
ADD https://api.github.com/repos/ICOS-Carbon-Portal/jupyterlab-extensions/git/refs/heads/trunk /tmp/ext_ref.json
RUN uv pip install --quiet git+https://github.com/ICOS-Carbon-Portal/jupyterlab-extensions.git@trunk --system

# Install ICOS libraries.
RUN uv pip install --quiet icoscp_core \
    "git+https://github.com/ICOS-Carbon-Portal/pylib.git@bump-pandas-version#subdirectory=icoscp" \
    "git+https://github.com/ICOS-Carbon-Portal/pylib.git@bump-pandas-version#subdirectory=icoscp_stilt" \
    fluxie \
    --system

ENV PORTAL_DATA_PATH_ICOS="/data/dataAppStorage/" \
    PORTAL_DATA_PATH_SITES="/data/dataAppStorage/" \
    PORTAL_DATA_PATH_ICOSCITIES="/data/cities/dataAppStorage" \
    PROJ_LIB="/opt/conda/share/proj"
