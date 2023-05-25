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
# Summer-school-2023
COPY ./summer_school_2023.sh /
RUN chmod +x /summer_school_2023.sh
USER jovyan
#WORKDIR /home/jovyan/education/
#RUN git clone https://git.wur.nl/peter050/hyytiala-practicals.git
#WORKDIR /home/jovyan/education/hyytiala-practicals
#RUN git fetch origin && git pull
#RUN ln -s /home/jovyan/education/hyytiala-practicals/EXERCISES -t /home/jovyan/education/Summer-school-2023/.
#RUN ln -s /home/jovyan/education/hyytiala-practicals/MEASUREMENTS -t /home/jovyan/education/Summer-school-2023/.
#RUN echo 'cd /home/jovyan/education/hyytiala-practicals && git pull' > ~/.bash_profile
WORKDIR /home/jovyan/education/Summer-school-2023/build/MODEL_ext
RUN ./MOGUNTIA < basefunct_gl
RUN ./MOGUNTIA < basefunct_nh
RUN ./MOGUNTIA < basefunct_tr
RUN ./MOGUNTIA < basefunct_sh
RUN ./MOGUNTIA < basefunct_base
RUN chmod g+w OUTPUT/*
RUN ls
# Set the entrypoint to the script with CMD arguments
ENTRYPOINT ["/summer_school_2023.sh"]