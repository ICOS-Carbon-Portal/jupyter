# Standard library imports
import os

# Related third party imports
from dockerspawner import DockerSpawner


c = get_config()

c.DockerSpawner.allowed_images = [
    'examples:latest',
    'icos-notebooks:latest',
    'summer-school:latest',
]
c.DockerSpawner.host_ip = '0.0.0.0'
c.DockerSpawner.network_name = 'jupyter'
c.DockerSpawner.notebook_dir = '/home/jovyan'
c.DockerSpawner.read_only_volumes = {'/data': '/data'}
c.DockerSpawner.remove = True
c.DockerSpawner.use_internal_ip = True
c.DummyAuthenticator.password = 'carboncloud'
c.JupyterHub.authenticator_class = 'dummy'
c.JupyterHub.hub_connect_ip = 'hub'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.shutdown_on_logout = True
c.JupyterHub.template_paths = ['/srv/jupyterhub/templates']

notebook_map = {
    # Explore ICOS Data Notebooks
    'nocfibs' : '/lab/tree/icos-jupyter-notebooks/NOAA Curve Fitting for ObsPack CO2.ipynb',
    'icatobs' : '/lab/tree/icos-jupyter-notebooks/ICOS Atmospheric Observation Statistics.ipynb',
    'chatmes' : '/lab/tree/icos-jupyter-notebooks/Characterization of Atmospheric Measurement Stations.ipynb',
    'hifoe'   : '/lab/tree/project-jupyter-notebooks/RINGO-T1.3/High Fossil CO2 Events at ICOS Stations.ipynb',
    # Examples
    'ex1'     : '/lab/tree/ex1 - Access a Single Dataset.ipynb',
    'ex1a'    : '/lab/tree/ex1a - Work with Atmospheric Data.ipynb',
    'ex1b'    : '/lab/tree/ex1b - Work with Ecosystem Data.ipynb',
    'ex1c'    : '/lab/tree/ex1c - Work with Ocean Data.ipynb',
    'ex2'     : '/lab/tree/ex2 - Explore ICOS Stations.ipynb',
    'ex3'     : '/lab/tree/ex3 - Combine ICOS & PANGAEA Data.ipynb',
    'ex4'     : '/lab/tree/ex4 - Access Collection Data & Metadata.ipynb',
    'ex5'     : '/lab/tree/ex5 - Query Metadata with SPARQL.ipynb',
    'ex6a'    : '/lab/tree/ex6a - Search STILT Stations.ipynb',
    'ex6b'    : '/lab/tree/ex6b - Animate STILT Footprints.ipynb',
    'ex6c'    : '/lab/tree/ex6c - Plot STILT Time Series & Footprints.ipynb',
    'ex7'     : '/lab/tree/ex7 - Read ObsPack Collections.ipynb',
    'ex8'     : '/lab/tree/ex8 - Authenticate for Remote Data Access.ipynb',
    # Notebooks with DOI
    'cichato' : '/lab/tree/project-jupyter-notebooks/city-characterization-tool/City Characterization Tool.ipynb',
    'ecosav'  : '/lab/tree/icos-jupyter-notebooks/Ecosystem Site Anomaly Visualization.ipynb',
    'nevito'  : '/lab/tree/project-jupyter-notebooks/network-view-tool/Network View Tool.ipynb',
    'riflas'  : '/lab/tree/project-jupyter-notebooks/RINGO-T1.3/RINGO Flask-Sampling(Task 1.3).ipynb',
    'raca'    : '/lab/tree/icos_jupyter_notebooks/Radiocarbon.ipynb',
    # Education
    'suschoo' : '',
    'enwishc' : '/lab/tree/project-jupyter-notebooks/envrifair-winterschool/map',
    'otcdrew' : '/lab/tree/project-jupyter-notebooks/otc-data-reduction-workshop',
}

image_map = {
    'icos-notebooks:latest': os.environ['ICOS_NOTEBOOKS_IMAGE'],
    'examples:latest': os.environ['EXAMPLES_IMAGE'],
    'summer-school:latest': os.environ['SUMMER_SCHOOL_IMAGE'],
}


class CustomDockerSpawner(DockerSpawner):
    @staticmethod
    def options_form(spawner):
        template_path = '/srv/jupyterhub/templates/custom_options_form.html'
        with open(template_path, 'r') as f:
            return f.read()

    @staticmethod
    def options_from_form(form_data):
        options = {}
        if form_data:
            image, notebook = form_data.get('env')[0].split('&nb=')
            options['image'] = image_map[image]
            options['notebook'] = notebook_map[notebook]
        return options

    async def start(self):
        if 'image' not in self.user_options:
            raise ValueError(
                'You must select an environment before starting the server.'
            )
        self.image = self.user_options['image']
        if 'notebook' in self.user_options.keys():
            self.default_url = self.user_options['notebook']
        return await super().start()


c.JupyterHub.spawner_class = CustomDockerSpawner
