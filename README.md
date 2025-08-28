# Local development
This repository is being developed locally on my machine (Zois), and
there is a systemd service that syncs the local changes to the remote on
ganymede.  
The service can be found here: `/etc/systemd/system/mon-gan.service`.
Whenever you update something, DO NOT do it on the remote but rather on 
the local. There is no service set to do this the other way around from
the remote to the local.
For the service to work properly, you need root access to ganymede
(fsicos3.lunarc.lu.se at port 60540). To do that, you already need to
have user access to ganymede and add your public key to the file
/root/.ssh/authorized_keys

# Todos
1. Find a way to dynamically inject the STATS_API_TOKEN to the services 
that need it.
2. In the icosbase Dockerfile, the last lines need to be moved to their
respective "correct" locations within the file. I only put them there
to not have to rebuild this image over and over again.

# How to run
Connect to ganymede via ssh as root and navigate to the project's 
directory:
```bash
cd /home/zois/pid4notebooks
```
From there, run:
```bash
docker-compose up --build -d
```
This will build and start all required services as daemon. 

# How to add a new notebook in the collection
1. Create the docker/notebook-name/Dockerfile file and notebook-name 
directory, if it doesn't exist.
2. The new Dockerfile should be based off of icosbase for now. Also, the
correct ownership for the directories within the created container needs 
to be applied. See other notebooks' Dockerfiles how to do both of these.
3. Create the notebooks/notebook-name directory and inside it, place all
the files associated with the notebook.
4. In the hub/jupyterhub_config.py file create an entry inside the 
`start()` method of the `CustomSpawner` class. For example:
```python
elif 'radiocarbon' in self.user.name:
    self.image = 'radiocarbon'
```

# Renaming the notebook names in the links in the template login.html
Avoid renaming the notebook names in login.html unless absolutely
necessary. The login template’s JavaScript uses `crypto.randomUUID()`
to convert each notebook name into a unique username. On the hub side,
the random ID is stripped to identify which Docker image to deploy.
Because notebook names in login.html map one-to-one with Docker images,
any changes can break deployments. The same mapping is also used for
reporting stats to [ICOS matomo](https://matomo.icos-cp.eu).
