ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.4
FROM $BASE
WORKDIR /home/jovyan/work
COPY --chown=1000:100 content/requirements.txt /home/jovyan/work/requirements.txt
RUN pip install --no-cache-dir -r /home/jovyan/work/requirements.txt \
 && python -m icos_ext.baseline
COPY build.urban-atmospheric-observations-and-simulations/overrides.json /opt/conda/share/jupyter/lab/settings/overrides.json
COPY --chown=1000:100 content/. /home/jovyan/work
