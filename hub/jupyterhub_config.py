# Standard library imports
import os

# Related third party imports
from dockerspawner import DockerSpawner


c = get_config()

c.DockerSpawner.allowed_images = [
    "pylib-examples:latest",
    "icos-notebooks:latest",
    "summer-school:latest",
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

nbs = {
    "icos_jupyter": [
        "curve_fitting_obspack.ipynb",
        "ecosystem_site_anomaly_visualization.ipynb",
        "icos_atmObs_statistics.ipynb",
        "radiocarbon.ipynb",
        "station_characterization.ipynb",
    ],
    "pylib_examples": [
        "ex1_data.ipynb",
        "ex1a_atmo_data.ipynb",
        "ex1b_eco_data.ipynb",
        "ex1c_ocean_data.ipynb",
        "ex2_station.ipynb",
        "ex3_multisource.ipynb",
        "ex4_collection.ipynb",
        "ex5_sparql.ipynb",
        "ex6a_STILT_find.ipynb",
        "ex6b_STILT_footprint_animation.ipynb",
        "ex7_ObsPackData.ipynb",
        "how_to_authenticate.ipynb",
    ]
}


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
            if notebook in nbs["icos_jupyter"]:
                options["notebook"] = f"/lab/tree/icos-jupyter-notebooks/{notebook}"
            elif notebook in nbs["pylib_examples"]:
                options["notebook"] = f"/lab/tree/{notebook}"
            elif notebook == "ICOS_flasksampling_fossilfuel.ipynb":
                options["notebook"] = (
                    f"/lab/tree/project-jupyter-notebooks/RINGO-T1.3/{notebook}"
                )
            elif notebook == "city-characterization-tool":
                options["notebook"] = (
                    f"/lab/tree/project-jupyter-notebooks/city-characterization-tool/city_characteristic_analysis.ipynb"
                )
            elif notebook == "network-view-tool":
                options["notebook"] = (
                    f"/lab/tree/project-jupyter-notebooks/network-view-tool/network_view.ipynb"
                )
            elif notebook == "envrifair_winterschool":
                options["notebook"] = (
                    f"/lab/tree/project-jupyter-notebooks/envrifair-winterschool/map"
                )
            elif notebook == "otc_data_reduction_workshop":
                options["notebook"] = (
                    f"/lab/tree/project-jupyter-notebooks/otc-data-reduction-workshop"
                )
            elif notebook == "summer_school":
                pass
            else:
                raise ValueError("Wrong or no image selected")

        return options

    async def start(self):
        if "image" not in self.user_options:
            raise ValueError(
                "You must select an environment before starting the server."
            )
        self.image = self.user_options["image"]
        if "notebook" in self.user_options.keys():
            self.default_url = self.user_options["notebook"]
        return await super().start()


c.JupyterHub.spawner_class = CustomDockerSpawner
