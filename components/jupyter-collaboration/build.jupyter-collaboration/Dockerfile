ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.2
FROM $BASE

# Run privileged steps as root so the ADD'd files (owned by root) can have
# their permissions changed; chmod as the non-root jovyan user would fail.
USER root

# Copy the example notebooks and make the tree read-only:
# files 0644->0444, dirs 0755->0555 (immutable but readable/browsable).
ADD content/. /opt/icos-examples/
RUN chmod -R a-w /opt/icos-examples

# Startup hook (COPY works regardless of USER).
COPY build.jupyter-collaboration/link-examples.sh /usr/local/bin/before-notebook.d/

# Drop back to the default non-root jovyan user for runtime.
USER ${NB_UID}
