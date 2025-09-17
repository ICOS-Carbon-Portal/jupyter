# Standard library imports
import os

# Related third party imports
from dockerspawner import DockerSpawner


c = get_config()

c.DockerSpawner.allowed_images = [
    "pylib-examples:latest",
    "icos-notebooks:latest",
    "awesome",
]
c.DockerSpawner.host_ip = "0.0.0.0"
c.DockerSpawner.network_name = "jupyter"
c.DockerSpawner.notebook_dir = "/home/jovyan"
c.DockerSpawner.read_only_volumes = {"/data": "/data"}
c.DockerSpawner.remove = True
c.DockerSpawner.use_internal_ip = True
c.DummyAuthenticator.password = "carboncloud"
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.hub_connect_ip = "hub"
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.shutdown_on_logout = True
c.JupyterHub.template_paths = ["/srv/jupyterhub/templates"]


class CustomDockerSpawner(DockerSpawner):
    @staticmethod
    def options_form(spawner):
        template_path = "/srv/jupyterhub/templates/custom_options_form.html"
        with open(template_path, "r") as f:
            return f.read()

    @staticmethod
    def options_from_form(form_data):
        options = {}
        if form_data:
            image, notebook = form_data.get("env")[0].split("&nb=")
            options["image"] = image
            if notebook in ["curve_fitting_obspack.ipynb", " radiocarbon.ipynb"]:
                options["notebook"] = f"/lab/tree/icos-jupyter-notebooks/{notebook}"
            else:
                options["notebook"] = f"/lab/tree/{notebook}"
            if image == "awesome":
                raise ValueError(
                    "You have been served with an awesome image! Congratulations!!!"
                )
        return options

    async def start(self):
        if "image" not in self.user_options:
            raise ValueError(
                "You must select an environment before starting the server."
            )
        self.image = self.user_options["image"]
        self.default_url = self.user_options["notebook"]
        return await super().start()


c.JupyterHub.spawner_class = CustomDockerSpawner
