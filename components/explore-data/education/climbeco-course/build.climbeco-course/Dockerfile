ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.2
FROM $BASE

RUN mamba install --quiet --yes -c conda-forge \
    pyogrio \
    fiona \
    && mamba clean --quiet --all --force-pkgs-dirs --yes

RUN uv pip install skyborn-cdo --system

ADD --chown=1000:100 content/. /home/jovyan/
