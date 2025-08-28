# Standard library imports
import os

# Related third party imports
from dockerspawner import DockerSpawner


c = get_config()

c.JupyterHub.authenticator_class = "dummy"
c.DummyAuthenticator.password = "test"
c.DockerSpawner.network_name = "jupyter"
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.host_ip = "0.0.0.0"
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = "hub"
c.JupyterHub.template_paths = ["/srv/jupyterhub/templates"]
c.DockerSpawner.read_only_volumes = {"/data": "/data"}

# Clean-up
# Shuts down all user servers on logout
c.JupyterHub.shutdown_on_logout = True
c.DockerSpawner.remove = True
c.DockerSpawner.notebook_dir = "/home/jovyan"

nb_map = {
    "explore-icos-atmobs": "/lab/tree/explore_icos_atmObs.ipynb",
    "curve-fitting-obspack": "/lab/tree/curve_fitting_obspack.ipynb",
    "radiocarbon": "/lab/tree/radiocarbon.ipynb",
}


class CustomSpawner(DockerSpawner):
    def start(self):
        # Extract notebook name from username
        notebook = self.user.name.split("&id=")[0]
        if notebook not in nb_map:
            raise ValueError(f"Unknown notebook: {notebook}")

        self.image = notebook  # use the notebook's Docker image
        self.default_url = nb_map[notebook]

        return super().start()


c.JupyterHub.spawner_class = CustomSpawner
