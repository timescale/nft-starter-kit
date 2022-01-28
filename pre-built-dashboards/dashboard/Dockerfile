FROM apache/superset
USER root
COPY superset_start.sh .
COPY sources.yaml .
COPY dash.json .
RUN pip install psycopg2-binary==2.9.1 && \
    chmod +x superset_start.sh
USER superset

ENTRYPOINT ["./superset_start.sh"]
