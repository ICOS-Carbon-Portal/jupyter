# Jupyter

This repository contains the Docker image definitions used by ICOS's
Jupyter notebook services.

More information about the Jupyter services and how to access them is
available on the [ICOS Carbon Portal website](https://www.icos-cp.eu/data-services/services/jupyter-notebook).

The images are used by two services with different purposes:

- **ExploreData** launches a temporary container for a selected
  notebook. The container is discarded when the session ends, so
  changes made during the session are not persisted.
- **The collaboration hub** provides each user with a persistent home
  directory, allowing notebooks, files, and other changes to be
  retained between sessions.

## Layout

```text
components/
├── icosbase/               # shared base image
├── jupyter-collaboration/  # collaboration hub image
└── explore-data/           # explore data images
    ├── explore-icos-data/
    ├── notebooks-with-doi/
    ├── timecapsule/
    └── education/
        ├── climbeco-course/
        ├── ocean-carbon-course/
        └── summer-school/
```

Each variant folder holds two directories:

- `content/` holds the notebooks and data copied to `/home/jovyan/` at
  build time.
- `build.<variant>/` holds the `Dockerfile` and a `stratos_meta.json`
  giving the image title, description and licence.

## Images

Each name links to that image's folder in this repository.

| Image | Used for |
|---|---|
| [icosbase](components/icosbase/) | The shared base every other image builds on. |
| [jupyter-collaboration](components/jupyter-collaboration/) | The collaboration hub, where each user has a persistent home. Example notebooks are served read-only alongside it. |
| [explore-icos-data](components/explore-data/explore-icos-data/) | The general Carbon Portal science notebooks. |
| [notebooks-with-doi](components/explore-data/notebooks-with-doi/) | Notebooks published with a DOI, tied to a paper or a citable dataset. |
| [timecapsule](components/explore-data/timecapsule/) | A frozen snapshot of every notebook as it stood in November 2025. |
| [climbeco-course](components/explore-data/education/climbeco-course/) | The ClimBEco Graduate Research School course. |
| [ocean-carbon-course](components/explore-data/education/ocean-carbon-course/) | The ocean carbon course. |
| [summer-school](components/explore-data/education/summer-school/) | The ICOS summer school. |

## Adding or updating an image

Each image variant lives under `components/` and contains its own
content and build configuration.

*⚠️ **Warning:** Do not move or remove the `hdf5` and `netcdf4`
entries at the end of `icosbase`'s `mamba_requirements.txt`. Their
position is intentional: they are used as solver constraints rather
than regular package requirements.*

### Adding a new image

1. Create a variant directory under `components/` with the following
   structure:

   ```
   components/
   └── <variant>/
       ├── content/
       └── build.<variant>/
   ```

2. Add the notebooks, data, and other files that should be available
   to the user to `content/`.

3. Create `build.<variant>/Dockerfile`. For most images, the
   Dockerfile only needs:

   ```
   ARG BASE=registry.icos-cp.eu/stratos.icosbase:<version>
   FROM $BASE
   ADD --chown=1000:100 content/. /home/jovyan/
   ```

4. Create `build.<variant>/stratos_meta.json` and provide the image
   title, description, and licence information.

### Updating an existing image

- To update notebooks, data, or other user files, modify the
  variant's `content/` directory.
- To add or update software packages, modify the variant's
  `Dockerfile`.
- Packages required by all image variants should be added to the base
  `icosbase` image instead of individual variants.

### Building and deployment

Building and deploying the images is handled by
[stratos](https://github.com/icos-carbon-portal/stratos), a separate
Python CLI used to build, manage, and deploy ICOS container images. It
handles the image lifecycle from building and inspecting images to
pushing them to the ICOS registry and deploying them to target hosts.

## Credits

The ICOS Jupyter services and their container images have been
developed and maintained by contributors within the
ICOS / Carbon Portal ecosystem over many years.

Thanks to everyone who has contributed to the services, notebooks,
Docker images, infrastructure, and documentation. See the
repository's Git history for individual contributions.

Claude and Codex have been used as development and documentation tools.

## Licence

This work is licensed under a Creative Commons Attribution 4.0
International License (CC BY 4.0).

Copyright © 2019-2026 ICOS ERIC
