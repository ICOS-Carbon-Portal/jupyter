ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.1
FROM $BASE
ADD content/. /opt/icos-examples/
RUN chmod -R a-w /opt/icos-examples
COPY build.collaboration/link-examples.sh /usr/local/bin/before-notebook.d/
