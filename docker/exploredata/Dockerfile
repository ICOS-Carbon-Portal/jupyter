ARG BASE=icosbase
FROM $BASE

# 1000:100 is jovyan:users
ADD --chown=1000:100 education ./education
ADD --chown=1000:100 icos_jupyter_notebooks ./icos_jupyter_notebooks
ADD --chown=1000:100 project_jupyter_notebooks ./project_jupyter_notebooks
ADD --chown=1000:100 introduction ./introduction
ADD --chown=1000:100 pylib_examples ./pylib_examples

# add files from the notebooks root level
ADD --chown=1000:100 *.md ./
ADD --chown=1000:100 *.ipynb ./
