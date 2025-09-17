# Standard library imports
import os

# Related third party imports
from dockerspawner import DockerSpawner


c = get_config()

c.JupyterHub.authenticator_class = "dummy"
c.DummyAuthenticator.password = "carboncloud"
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


class CustomDockerSpawner(DockerSpawner):
    def options_form(self, spawner):
        template_path = "/srv/jupyterhub/templates/custom_options_form.html"
        with open(template_path, "r") as f:
            return f.read()

    def options_from_form(self, formdata):
        # No defaults: require explicit choice
        options = {}
        env_choice = formdata.get("env")
        if env_choice:
            options["env"] = env_choice[0]
        return options

    async def start(self):
        if "env" not in self.user_options:
            raise ValueError(
                "You must select an environment before starting the server."
            )
        self.image = self.user_options["env"]
        return await super().start()


c.JupyterHub.spawner_class = CustomDockerSpawner
