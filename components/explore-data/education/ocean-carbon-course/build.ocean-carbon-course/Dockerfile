ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.0
FROM $BASE
ADD --chown=1000:100 content/. /home/jovyan/
RUN uv pip install fluxengine --system
