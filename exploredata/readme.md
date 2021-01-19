# Content:

## Dockerfile
How to build the image which is deployed to exploredata.

## Makefile

- make pushtest deploy the image to exploretest
- make pushprod deploy to production *exploredata*

## templates
contains `login.html` creating an ICOS CP branded login page, overriding the out of the box login page. [https://github.com/jupyterhub/jupyterhub/tree/master/share/jupyterhub/templates](https://github.com/jupyterhub/jupyterhub/tree/master/share/jupyterhub/templates)

## nbextensionDefault
By default we install the conda-forge jupyter_contrib_nbextensions. The global defaults
can be changed by supplying a patch to the original config file. Have a look a the Dockerfile.
a guide follows (Thanks Andre)
Extract the original file
docker-extract is a non-standard script that exists in our docker installations
```
$ docker-extract notebook /opt/conda/share/jupyter/nbextensions/toc2/toc2.yaml .
```

### Step 1
```
# Rename file and create a copy
$ mv toc2.yaml old.yaml
$ cp old.yaml new.yaml

# Now edit the new file
$ $EDITOR new.yaml

#Preview the diff
$ diff -u old.yaml new.yaml

# Save the diff to file
$ diff -u old.yaml new.yaml > toc2.diff
```
### Step 2
Adapt the Dockerfile, which (after testing) should be uploaded to this directory on GitHub. Similar to the following lines of code, you need to add your diff file, and then patch the existing configuration

```
# Add the diff to the image
COPY toc2.diff /tmp/
# Modify the config file in-place.
RUN patch /opt/conda/share/jupyter/nbextensions/toc2/toc2.yaml /tmp/toc2.diff
```
### Step 3
Build and test the docker image
```
$ docker build --tag test .
$ docker run -it test bash
$ cat /opt/conda/share/jupyter/nbextensions/toc2/toc2.yaml
```

### Step 4
Make sure you update the repository with the new Dockerfile and the nbextensionDefault/newConfig.diff