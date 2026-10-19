ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.3
FROM $BASE

RUN mamba install --quiet --yes -c conda-forge \
    esmpy=8.9.1 \
    xesmf=0.9.2 \
    hdf5=1.14.6 \
    netcdf4=1.7.4 \
    && mamba clean --quiet --all --force-pkgs-dirs --yes

USER root
COPY --chmod=0755 hooks/tm5-clone.sh /usr/local/bin/start-notebook.d/tm5-clone.sh
COPY --chmod=0444 build.fit-ic/gui.yml /opt/fitic/gui.yml
USER ${NB_USER}
ADD --chown=1000:100 content/. /home/jovyan/
