ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.1
FROM $BASE

RUN uv pip install --system \
    panel==1.8.10 \
    param==2.3.3 \
    hvplot==0.12.2 \
    geoviews==1.15.1 \
    holoviews==1.22.1 \
    bokeh==3.9.0

USER root
COPY --chmod=0755 hooks/tm5-clone.sh /usr/local/bin/start-notebook.d/tm5-clone.sh
USER ${NB_USER}
ADD --chown=1000:100 content/. /home/jovyan/
