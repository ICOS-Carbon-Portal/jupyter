ARG BASE=icosbase
FROM $BASE
ADD --chown=1000:100 . /home/jovyan/
USER root
RUN apt update
RUN apt install -y vim
RUN mv .summer_school.sh /usr/local/bin/summer_school.sh
#COPY summer_school.sh /usr/local/bin/summer_school.sh
RUN chmod +x /usr/local/bin/summer_school.sh
RUN sudo apt-get update
RUN sudo apt-get install --reinstall -y ca-certificates
RUN sudo update-ca-certificates
ENTRYPOINT ["tini", "-g", "--"]
CMD ["summer_school.sh", "--collaborative"]