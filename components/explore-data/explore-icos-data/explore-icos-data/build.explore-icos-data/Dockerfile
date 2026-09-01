ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.0
FROM $BASE

RUN uv pip install --quiet --system \
    pydap==3.5.9 \
    icoscp_core==0.3.13

ADD --chown=1000:100 content/. /home/jovyan/
