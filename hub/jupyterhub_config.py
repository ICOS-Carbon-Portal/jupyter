from dockerspawner import DockerSpawner


c = get_config()

c.JupyterHub.authenticator_class = 'dummy'
c.DummyAuthenticator.password = 'test'
c.DockerSpawner.network_name = 'jupyter'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'hub'
c.JupyterHub.template_paths = ['/srv/jupyterhub/templates']

# Clean-up
# Shuts down all user servers on logout
c.JupyterHub.shutdown_on_logout = True
c.DockerSpawner.remove = True
c.DockerSpawner.notebook_dir = '/home/jovyan'
c.DockerSpawner.read_only_volumes = {
    '/data' : '/data'
}


class CustomSpawner(DockerSpawner):
    def start(self):
        if 'explore-icos-atmobs' in self.user.name:
            self.image = 'explore-icos-atmobs:latest'
            notebook_name = 'explore-icos-atmobs'.replace('-', '_')
            self.environment['NOTEBOOK_NAME'] = notebook_name
        elif 'curve-fitting-obspack' in self.user.name:
            self.image = 'curve-fitting-obspack:latest'
            notebook_name = 'curve-fitting-obspack'.replace('-', '_')
            self.environment['NOTEBOOK_NAME'] = notebook_name
        else:
            exit(1)
        return super().start()


c.JupyterHub.spawner_class = CustomSpawner
