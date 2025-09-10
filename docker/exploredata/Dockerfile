ARG BASE=icosbase
FROM $BASE

# 1000:100 is jovyan:users
ADD --chown=1000:100 education ./education
ADD --chown=1000:100 icos_jupyter_notebooks ./icos_jupyter_notebooks
ADD --chown=1000:100 project_jupyter_notebooks ./project_jupyter_notebooks
ADD --chown=1000:100 introduction ./introduction
ADD --chown=1000:100 pylib_examples ./pylib_examples

# Add files from the notebooks' root level.
ADD --chown=1000:100 *.md ./
ADD --chown=1000:100 *.ipynb ./

# The index and other notebooks have an initialization cell. To automatically
# run these notebooks we need to trust them first. This also prevents the
# trust notebook popup window from showing up.
RUN jupyter trust index_notebook.ipynb
RUN jupyter trust project_jupyter_notebooks/RINGO_T1.3/ICOS_flasksampling_fossilfuel.ipynb
RUN jupyter trust project_jupyter_notebooks/RINGO_T1.3/RINGO_T1.3_flasksampling_v5.ipynb
COPY --chown=jovyan:users log_execution.py .ipython/profile_default/startup/
