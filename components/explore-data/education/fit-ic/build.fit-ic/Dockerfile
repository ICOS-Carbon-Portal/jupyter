ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.3
FROM $BASE

ENV USER=${NB_USER}

RUN mamba install --quiet --yes -c conda-forge \
    esmpy=8.9.1 \
    xesmf=0.9.2 \
    hdf5=1.14.6 \
    netcdf4=1.7.4 \
    && mamba clean --quiet --all --force-pkgs-dirs --yes

RUN git clone --depth 1 --branch esa2026 https://github.com/gmonteil/tm5.git /home/jovyan/tm5 \
    && uv pip install --system -e "/home/jovyan/tm5[fitic]"

ADD --chown=1000:100 content/. /home/jovyan/
