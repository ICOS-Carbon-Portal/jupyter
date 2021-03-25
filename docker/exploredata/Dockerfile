ARG BASE=icosbase
FROM $BASE

# -----start temp fix-----------------------------------

# temporary fixes to the icos base image
# current verion of jupyter/datascience-notebook

# has updated version of pandas which needs openpyxl to read excel files
RUN mamba install -qy openpyxl

# gdal 3.2.1 can't be loaded.. downgrade to last version we 
# know is working

RUN mamba install -qy gdal=3.1.4

# -----eof temp fix------------------------------------


# 1000:100 is jovyan:users
ADD --chown=1000:100 education ./education
ADD --chown=1000:100 icos_jupyter_notebooks ./icos_jupyter_notebooks
ADD --chown=1000:100 project_jupyter_notebooks ./project_jupyter_notebooks
ADD --chown=1000:100 introduction ./introduction
ADD --chown=1000:100 pylib_examples ./pylib_examples

# add files from the notebooks root level
ADD --chown=1000:100 *.md ./
ADD --chown=1000:100 *.ipynb ./
