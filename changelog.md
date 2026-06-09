# Changelog

ICOS Jupyter environments are a family of purpose-built images that share a common `icosbase` base image:

- [ExploreData](exploredata.md) uses `examples:0.1.1`
- The [Collaborative Jupyter Hub](hub-user-guide.md) uses `collaboration:0.1.0`

Both build on `icosbase:0.1.1`.

## icosbase <a href="https://github.com/ICOS-Carbon-Portal/pid4notebooks/tree/6c82fd64b176b2faef10c1e351871cc71cf003f5/docker/icosbase" target="_blank" rel="noopener">0.1.1</a> <p>(08/06/2026)</p>

- Move off the 2022 `jupyter/datascience-notebook` Docker Hub pin used by 0.1.0 onto a 2026 `quay.io` base
- Drop the full TeX Live install, the extra R packages, the qgrid2 extension, and the legacy kernel; ship a single Python kernel
- Trim requirements to only what ICOS notebooks need beyond the base image (12 mamba and 1 pip package, down from the previous full stack)
- Install [uv](https://pypi.org/project/uv/) by copying it from the official `ghcr.io/astral-sh/uv` image instead of via pip
- Replace qgrid2, icos-splash, and the nersc-announcements fork with the ICOS JupyterLab extensions from [ICOS-Carbon-Portal/jupyterlab-extensions](https://github.com/ICOS-Carbon-Portal/jupyterlab-extensions)
- Pin the ICOS libraries [icoscp](https://pypi.org/project/icoscp/0.2.3/) 0.2.3 and [icoscp_stilt](https://pypi.org/project/icoscp_stilt/0.1.4/) 0.1.4, bump [icoscp_core](https://pypi.org/project/icoscp_core/0.3.12/) to 0.3.12, and add [fluxie](https://pypi.org/project/fluxie/)
- Add [zarr](https://pypi.org/project/zarr/2.18.7/) 2.18.7, [plotly](https://pypi.org/project/plotly/6.8.0/) 6.8.0, [pydap](https://pypi.org/project/pydap/3.5.9/) 3.5.9, and [jupyter-resource-usage](https://github.com/jupyter-server/jupyter-resource-usage) 1.2.1 to mamba requirements; install [pangaeapy](https://github.com/pangaea-data-publisher/pangaeapy) from upstream git
- Keep the geospatial and visualization stack (cartopy, folium, geoviews, holoviews, xarray) and pangaeapy

## icosbase <a href="https://github.com/ICOS-Carbon-Portal/pid4notebooks/tree/6a75ccbb1bb017c3ac61223420575096af47c0b0/docker/icosbase" target="_blank" rel="noopener">0.1.0</a> <p>(26/02/2026)</p>

- Essentially the same environment as 2.1.0 below (same 2022 base and package stack), published as the first `icosbase` image under `registry.icos-cp.eu/stratos.icosbase`
- Carries the full TeX Live install, the qgrid2 extension, the R packages, and the conda permission fix from the 2.x line
- Kept deliberately frozen so existing notebooks keep working, which means it is behind on newer Python libraries

## Previous images

The entries below track the previous single monolithic image, before the move to the `icosbase` base plus variants model.

### 2.1.0 <p>(07/03/2023 - 11/02/2025)</p>

- Add [fluxengine](https://pypi.org/project/fluxengine/) version 4.0.9.1 to pip
  requirements, [pyco2sys](https://pypi.org/project/PyCO2SYS/) version 1.8.3.4
  to mamba requirements, and [`uv`](https://pypi.org/project/uv/) utility to
  docker image installation (11/02/2025)
- Add `rsync` utility to docker image installation (06/11/2024)
- Add [itables]() version 2.2.2 to pip requirements (28/10/2024)
- Bump [icoscp](https://pypi.org/project/icoscp/) to version 0.2.2 
(18/10/2024)
- Bump [icoscp_stilt](https://pypi.org/project/icoscp_stilt/) to version 0.1.3 
(18/10/2024)
- Bump [icoscp\_core](https://pypi.org/project/icoscp_core/) to version 0.3.7
(17/10/2024)
- Bump [icoscp](
https://github.com/ICOS-Carbon-Portal/pylib/tree/c68ad7afa1c27efb69f3350ad7723827517ad004)
to master branch (05/04/2024)
- Bump [icoscp\_core](https://pypi.org/project/icoscp_core/) to version 0.3.3
(05/04/2024)
- Other notebook fixes mentioned [here](
https://github.com/ICOS-Carbon-Portal/jupyter/issues/367) (05/04/2023)
- Bump [icoscp](https://pypi.org/project/icoscp/0.1.20/) to version 0.1.20
(12/01/2024)
- Add [jupyter-splitview](https://pypi.org/project/jupyter-splitview/0.1.2/)
version 0.1.2, [jupyterlab\_mathjax2](
https://pypi.org/project/jupyterlab-mathjax2/4.0.0/) version 4.0.0, and
[icoscp\_core](https://pypi.org/project/icoscp_core/0.3.0/) version 0.3.0 to
pip requirements (12/01/2024)
- Bump [icoscp](https://pypi.org/project/icoscp/0.1.19/) to version 0.1.19
(25/07/2023)
- Add [h5netcdf](https://pypi.org/project/h5netcdf/) version 1.1.0 to mamba
requirements (10/05/2023)
- Add [kaleido](https://pypi.org/project/kaleido/0.2.1/) version 0.2.1 and
[`cyclebars`](https://github.com/klavere/cyclebars) to the docker image
installation (28/04/2023)
- Update [ipywidgets](https://pypi.org/project/ipywidgets/8.0.4/) to version
8.0.4 and [plotly](https://pypi.org/project/plotly/5.14.1/) to version 5.14.1
(13/04/2023)
- Add `zip` library to the docker image installation (20/03/2023)
- Add [icos-splash](https://github.com/ZogopZ/icos-splash) to the docker image
installation (07/03/2023)
- Fork and patch [nersc-announcements-extension](
https://github.com/ZogopZ/nersc-refresh-announcements) to resolve TypeScript
issues (07/03/2023)
- Add [jupyter-resource-usage](
https://github.com/jupyter-server/jupyter-resource-usage) to pip requirements
(07/03/2023)
- Add [paramiko](https://github.com/paramiko/paramiko) to pip requirements
(07/03/2023)
- Other notebook fixes mentioned [here](
https://github.com/ICOS-Carbon-Portal/jupyter/issues/262) (07/03/2023)
  
### 2.0.1 <p>(15/11/2022)</p>

- Add PyGeodesy version 22.11.3 library to the docker image installation
- Add utm version 0.7.0 library to the docker image installation
- Fix errors caused by cartopy library

### 2.0.0 <p>(04/11/2022)</p>
- ##### Jupyter Classic vs JupyterLab
    - Earlier versions of the Jupyter solutions provided by the ICOS Carbon
      Portal used the Jupyter Classic view. 
    - One major advantage of JupyterLab compared to Jupyter Classic is the
      possibility to work with several notebooks using tabs.
    - The default view of ICOS Carbon Portal has changed to JupyterLab. For
      users who wish to use the Jupyter Classic view can do so by choosing
      Launch Classic view in the Help menu.
	  For further reading on JupyterLab we refer to 
      [the JupyterLab documentation](
      https://jupyterlab.readthedocs.io/en/stable/).

		 	 
	 
-  ##### Docker image of [jupyter/datascience-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-datascience-notebook) 
     - Image version: [jupyter/datascience-notebook:dc95493e13c4](https://hub.docker.com/layers/jupyter/datascience-notebook/dc95493e13c4/images/sha256-731da3b2844e168d677e622d6ce127e790117e291c57933deefd93bc5f79217d?context=explore) on `linux/amd64`.
		- Python 3.10.6 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/x86_64-datascience-notebook-dc95493e13c4#python-packages)  
		- JupyterLab 3.4.7
		- R 4.1.3 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/x86_64-datascience-notebook-dc95493e13c4#r-packages)
		- Julia 1.8.2 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/x86_64-datascience-notebook-dc95493e13c4#julia-packages)
 
	 
### 1.0.0
 - ##### Docker [jupyter/datascience-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-datascience-notebook) 
	- Image version: [jupyter/datascience-notebook:5cb007f03275](https://hub.docker.com/layers/jupyter/datascience-notebook/5cb007f03275/images/sha256-e6d5c7d595d25f6ec7a894d8fcc7cb4b542c28f65fb71cdf0cb9b77f0ce0ddd0?context=explore) on `linux/amd64`.
		- Python 3.8.6 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/datascience-notebook-5cb007f03275#python-packages)  
		- R 4.0.3 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/datascience-notebook-5cb007f03275#r-packages)
		- Julia 1.5.3 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/datascience-notebook-5cb007f03275#julia-packages)
 
