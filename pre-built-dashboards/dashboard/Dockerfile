FROM apache/superset
USER root
COPY superset_start.sh sources.yaml dash.json ./
RUN chmod +x superset_start.sh
USER superset

ENTRYPOINT ["./superset_start.sh"]
