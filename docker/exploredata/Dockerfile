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
# Summer-school
USER jovyan
WORKDIR /home/jovyan/education/
RUN git clone https://git.wur.nl/peter050/hyytiala-practicals.git
RUN ln -s /home/jovyan/education/hyytiala-practicals/EXERCISES -t /home/jovyan/education/Summer-school/.
RUN ln -s /home/jovyan/education/hyytiala-practicals/MEASUREMENTS -t /home/jovyan/education/Summer-school/.
RUN echo "cd /home/jovyan/education/hyytiala-practicals && git fetch origin && git pull" > ~/.bash_profile
RUN mkdir -p /home/jovyan/.ipython/profile_default/startup
COPY 00_summer_school.py /home/jovyan/.ipython/profile_default/startup/00_summer_school.py
WORKDIR /home/jovyan/education/Summer-school/build/MODEL_ext
RUN make clean && make
RUN ./MOGUNTIA < basefunct_gl
RUN ./MOGUNTIA < basefunct_nh
RUN ./MOGUNTIA < basefunct_tr
RUN ./MOGUNTIA < basefunct_sh
RUN ./MOGUNTIA < basefunct_base
RUN chmod g+w OUTPUT/*
WORKDIR /home/jovyan/education/Summer-school/

