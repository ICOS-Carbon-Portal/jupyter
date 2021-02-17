<img src="https://www.icos-cp.eu/sites/default/files/2017-11/ICOS_CP_logo.png" width="300" align="right"/>
<br>
<br>
<br> 

## Dockerfile
How to build the image which is deployed to exploredata.

## Makefile

- make pushtest deploy the image to *exploretest*
- make pushprod deploy to production *exploredata*

## templates
contains `login.html` . An ICOS CP branded login page, overriding the out of the box login page. [https://github.com/jupyterhub/jupyterhub/tree/master/share/jupyterhub/templates](https://github.com/jupyterhub/jupyterhub/tree/master/share/jupyterhub/templates)

## nbextensionDefault
By default we install the conda-forge jupyter_contrib_nbextensions. The global defaults
can be changed by supplying a patch to the original config file. Have a look a the Dockerfile.
A guide follows (Thanks to Andre)

Extract the original file
docker-extract is a non-standard script that exists in our docker installations
```
$ docker-extract notebook /opt/conda/share/jupyter/nbextensions/toc2/toc2.yaml .
$ docker-extract notebook /opt/conda/share/jupyter/nbextensions/toc2/toc2.js .
```

Following a step by step guide for one script....
### Step 1
```
# Rename file and create a copy
$ mv toc2.yaml toc2.yaml.old
$ cp toc2.yaml.old toc2.yaml.new

# Now edit the new file and make your changes

#Preview the diff
$ diff -u toc2.yaml.old toc2.yaml.new

# Save the diff to file
$ diff -u old.yaml new.yaml > toc2.yaml.diff
```
### Step 2
Adapt the Dockerfile, which (after testing) should be uploaded to this directory on GitHub. Similar to the following lines of code, you need to add your diff file, and then patch the existing configuration

```
COPY exploredata/nbextensionDefault/*.diff /tmp/
RUN patch /opt/conda/share/jupyter/nbextensions/toc2/toc2.yaml /tmp/toc2.yaml.diff
RUN patch /opt/conda/share/jupyter/nbextensions/toc2/toc2.js /tmp/toc2.js.diff
RUN jupyter nbextension enable toc2/main

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
