FROM jupyter/scipy-notebook

USER root
RUN useradd -m appuser
WORKDIR /work

RUN pip install flexpipe

RUN chown -R appuser:appuser /home
RUN chown -R appuser:appuser /work

VOLUME /work
EXPOSE 8888
USER appuser
