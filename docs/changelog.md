# Changelog

 -  **Note**: The python package of the ICOS Carbon Portal, `icoscp`, is always the latest version. For details we refer the user to [ICOS Carbon Portal pylib - Changelog](https://icos-carbon-portal.github.io/pylib/changelog/).
## 2.0.0
- #### Jupyter Classic vs JupyterLab
    - Earlier versions of the Jupyter solutions provided by the ICOS Carbon Portal used the Jupyter Classic view. 
    - One major advantage of JupyterLab compared to Jupyter Classic is the possibility to work with several notebooks using tabs.
    - The default view of ICOS Carbon Portal has changed to JupyterLab. For users who wish to use the Jupyter Classic view can do so by choosing Launch Classic view in the Help menu.
	  For further reading on JupyterLab we refer to [the JupyterLab documentation](https://jupyterlab.readthedocs.io/en/stable/).

		 	 
	 
-  #### Docker image of [jupyter/datascience-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-datascience-notebook) 
     - Image version: [jupyter/datascience-notebook:dc95493e13c4](https://hub.docker.com/layers/jupyter/datascience-notebook/dc95493e13c4/images/sha256-731da3b2844e168d677e622d6ce127e790117e291c57933deefd93bc5f79217d?context=explore) on `linux/amd64`.
		- Python 3.10.6 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/x86_64-datascience-notebook-dc95493e13c4#python-packages)  
		- JupyterLab 3.4.7
		- R 4.1.3 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/x86_64-datascience-notebook-dc95493e13c4#r-packages)
		- Julia 1.8.2 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/x86_64-datascience-notebook-dc95493e13c4#julia-packages)
 
	 
## 1.0.0
 - #### Docker [jupyter/datascience-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-datascience-notebook) 
	- Image version: [jupyter/datascience-notebook:5cb007f03275](https://hub.docker.com/layers/jupyter/datascience-notebook/5cb007f03275/images/sha256-e6d5c7d595d25f6ec7a894d8fcc7cb4b542c28f65fb71cdf0cb9b77f0ce0ddd0?context=explore) on `linux/amd64`.
		- Python 3.8.6 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/datascience-notebook-5cb007f03275#python-packages)  
		- R 4.0.3 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/datascience-notebook-5cb007f03275#r-packages)
		- Julia 1.5.3 - [link to packages](https://github.com/jupyter/docker-stacks/wiki/datascience-notebook-5cb007f03275#julia-packages)
 