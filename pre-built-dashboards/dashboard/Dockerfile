FROM apache/superset
USER root
COPY superset_start.sh sources.yaml dash.json ./
RUN wget https://assets.timescale.com/docs/downloads/nft_sample.zip; \
    unzip nft_sample.zip; \
    rm nft_sample.zip; \
    pip install psycopg2-binary==2.9.1 && \
    chmod +x superset_start.sh;
USER superset

ENTRYPOINT ["./superset_start.sh"]
