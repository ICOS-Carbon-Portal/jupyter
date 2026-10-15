ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.3
FROM $BASE

# Install the icos-ext 0.3.0a1 pre-release over the version icosbase ships,
# then record the package baseline. The baseline must come after the last
# package install.
RUN pip install --no-cache-dir \
      https://github.com/ICOS-Carbon-Portal/jupyterlab-extensions/releases/download/v0.3.0-a1/icos_ext-0.3.0a1-py3-none-any.whl && \
    python -m icos_ext.baseline

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
