# pid4notebooks

This repository contains the build definitions for ICOS's interactive
Jupyter notebook service Docker images.

## Layout

The `docker/` directory has one folder per image:

```text
docker/
└── <name>/
    ├── content/             # notebooks + data, copied to /home/jovyan/ at build time
    └── build.<name>/
        ├── Dockerfile
        └── stratos_meta.json  # image title, description, license
```

Every image except `icosbase` derives from it with the same three
lines:

```dockerfile
ARG BASE=registry.icos-cp.eu/stratos.icosbase:<version>
FROM $BASE
ADD --chown=1000:100 content/. /home/jovyan/
```

The build context is `content/`; the Dockerfile is referenced from
`../build.<name>/Dockerfile`.

To change what an image ships, edit its `content/` (notebooks and data)
or its `Dockerfile` (packages). Packages shared across all images
belong in `docker/icosbase/content/`.

## The Base Image (icosbase)

`docker/icosbase/` is the shared base that all other images build on.
It is built `FROM quay.io/jupyter/datascience-notebook` pinned by
digest (the `:latest` tag as of 2026-03-18) and published to the ICOS
registry as `registry.icos-cp.eu/stratos.icosbase` (versions `0.1.0`
and `0.1.1`). Its `content/` holds `mamba_requirements.txt` and
`pip_requirements.txt`.

From its metadata: a stable image that keeps the geospatial and
visualization stack (cartopy, folium, geoviews, holoviews, xarray),
pangaeapy, and the ICOS-specific libraries, while dropping TeX Live and
a large set of mamba/pip requirements compared to its predecessor.

## Images

| Image | Folder | Base | Description |
|---|---|---|---|
| icosbase | `docker/icosbase` | `quay.io/jupyter/datascience-notebook` (digest-pinned) | Shared base image, published as `registry.icos-cp.eu/stratos.icosbase`. |
| examples | `docker/examples` | icosbase 0.1.1 | ICOS Python library (pylib) usage examples, ex1 through ex8. |
| collaboration | `docker/collaboration` | icosbase 0.1.1 | The example notebooks served read-only at `~/icos-examples`. Built for ICOS's separate collaboration service, which gives each user a persistent home directory. Ships a `link-examples.sh` startup hook; its `content/` is a hand-maintained duplicate of `examples`. |
| icos-notebooks | `docker/icos-notebooks` | icosbase 0.1.0 | ICOS Carbon Portal science notebooks plus DOI/PID notebooks (education, introduction, project-jupyter-notebooks, icos-jupyter-notebooks). |
| summer-school | `docker/summer-school` | icosbase 0.1.0 | Summer school teaching material, including content from the hyytiala practicals repository. |
| ocean-carbon-course | `docker/ocean-carbon-course` | icosbase 0.1.0 | The fluxengine Python library plus ocean carbon science teaching notebooks. |
| classic | `docker/classic` | icosbase 0.1.0 | All notebooks through November 2025 collected in a single environment. |
| fit-ic | `docker/fit-ic` | icosbase 0.1.1 | The TM5 atmospheric transport model (cloned and installed at startup) plus interactive visualization libraries (Panel, HoloViews, hvPlot, GeoViews, Bokeh). Carries an extra `hooks/` directory. |
