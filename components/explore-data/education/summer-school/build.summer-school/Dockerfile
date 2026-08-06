ARG BASE=registry.icos-cp.eu/stratos.icosbase:0.1.0
FROM $BASE
ADD --chown=1000:100 content/. /home/jovyan/
USER root
RUN apt update
RUN apt install -y vim
RUN mv .summer_school.sh /usr/local/bin/summer_school.sh
RUN chmod +x /usr/local/bin/summer_school.sh
RUN apt-get install --reinstall -y ca-certificates
RUN update-ca-certificates
ENTRYPOINT ["tini", "-g", "--"]
CMD ["summer_school.sh", "--collaborative"]
