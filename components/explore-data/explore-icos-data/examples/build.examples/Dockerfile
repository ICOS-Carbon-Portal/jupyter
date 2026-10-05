ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.3
FROM $BASE
RUN pip install --no-cache-dir \
      https://github.com/ICOS-Carbon-Portal/jupyterlab-extensions/releases/download/v0.3.0-a0/icos_ext-0.3.0a0-py3-none-any.whl && \
    python -m icos_ext.baseline
ADD --chown=1000:100 content/. /home/jovyan/
